<?php

namespace App\Jobs;

use App\Events\FlowEventBroadcast;
use App\Models\Flow;
use App\Models\FlowLog;
use App\Models\FlowRun;
use App\Services\FlowService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class ProcessFlowManagerEvent implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function __construct(
        private readonly string $event,
        private readonly array $payload = [],
    ) {
    }

    public function handle(): void
    {
        $flowRun = $this->resolveFlowRun();
        $flow = $flowRun?->flow ?? $this->resolveFlow();

        if (! $flow) {
            Log::info('flow-manager event without flow match', [
                'event' => $this->event,
                'payload' => $this->payload,
            ]);
            return;
        }

        $this->updateFlowStatus($flow, $flowRun);
        $this->recordLog($flow, $flowRun);
        broadcast(new FlowEventBroadcast($flow->id, $this->event, $this->payload));
    }

    private function resolveFlowRun(): ?FlowRun
    {
        $runId = $this->payload['flow_run_id'] ?? $this->payload['run_id'] ?? null;
        if ($runId) {
            return FlowRun::find($runId);
        }

        $containerId = $this->payload['container_id'] ?? null;
        if ($containerId) {
            return FlowRun::where('container_id', $containerId)->latest()->first();
        }

        return null;
    }

    private function resolveFlow(): ?Flow
    {
        $flowId = $this->payload['flow_id'] ?? null;
        if ($flowId) {
            return Flow::find($flowId);
        }

        $containerId = $this->payload['container_id'] ?? null;
        if ($containerId) {
            return Flow::where('container_id', $containerId)->first();
        }

        return null;
    }

    private function updateFlowStatus(Flow $flow, ?FlowRun $flowRun): void
    {
        $status = $this->payload['new_state'] ?? $this->payload['status'] ?? null;

        if ($this->event === 'container_created') {
            $containerId = $this->payload['container_id'] ?? null;
            if ($containerId) {
                if ($flowRun) {
                    $flowRun->update([
                        'container_id' => $containerId,
                        'meta' => $this->payload,
                    ]);
                }

                $flow->update([
                    'container_id' => $containerId,
                ]);
            }

            return;
        }

        if ($this->event === 'lock_generated' && $flowRun) {
            $flowRun->update([
                'lock' => $this->payload['lock'] ?? null,
                'status' => 'locked',
                'meta' => $this->payload,
            ]);

            app(FlowService::class)->markLockReady($flow, $flowRun);

            return;
        }

        if ($this->event === 'lock_failed' && $flowRun) {
            $flowRun->update([
                'status' => 'lock_failed',
                'meta' => $this->payload,
            ]);

            return;
        }

        if ($this->event === 'container_crashed') {
            if ($flowRun) {
                $flowRun->update([
                    'status' => 'error',
                    'finished_at' => now(),
                    'meta' => $this->payload,
                ]);
            }

            $this->syncFlowStatusFromRun($flow, $flowRun, 'error');

            return;
        }

        if (! $status) {
            return;
        }

        if ($status === 'running') {
            if ($flowRun) {
                $flowRun->update([
                    'status' => 'running',
                    'started_at' => now(),
                    'meta' => $this->payload,
                ]);
            }

            $this->syncFlowStatusFromRun($flow, $flowRun, 'running');

            return;
        }

        if (in_array($status, ['stopped', 'exited', 'finished', 'dead'], true)) {
            if ($flowRun) {
                $flowRun->update([
                    'status' => 'stopped',
                    'finished_at' => now(),
                    'meta' => $this->payload,
                ]);
            }

            $this->syncFlowStatusFromRun($flow, $flowRun, 'stopped');
        }
    }

    private function syncFlowStatusFromRun(Flow $flow, ?FlowRun $run, string $status): void
    {
        if (! $run || $run->type !== 'production' || ! $run->active) {
            return;
        }

        $payload = $status === 'running'
            ? ['status' => $status, 'last_started_at' => now()]
            : ['status' => $status, 'last_finished_at' => now()];

        $flow->update($payload);
    }

    private function recordLog(Flow $flow, ?FlowRun $flowRun): void
    {
        $level = match ($this->event) {
            'container_health_warning', 'resource_alert' => 'warning',
            'container_crashed' => 'error',
            default => 'info',
        };

        FlowLog::create([
            'flow_id' => $flow->id,
            'flow_run_id' => $flowRun?->id,
            'level' => $level,
            'message' => sprintf('Event: %s', $this->event),
            'context' => $this->payload,
        ]);

        if ($flowRun && (isset($this->payload['actors']) || isset($this->payload['events']))) {
            $flowRun->update([
                'actors' => $this->payload['actors'] ?? $flowRun->actors,
                'events' => $this->payload['events'] ?? $flowRun->events,
            ]);
        }
    }
}
