<?php

namespace App\Jobs;

use App\Events\FlowEventBroadcast;
use App\Models\Flow;
use App\Models\FlowLog;
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
        $containerId = $this->payload['container_id'] ?? null;
        $flow = $containerId
            ? Flow::where('container_id', $containerId)->first()
            : null;

        if ($flow) {
            $this->updateFlowStatus($flow);
            $this->recordLog($flow);
            broadcast(new FlowEventBroadcast($flow->id, $this->event, $this->payload));

            return;
        }

        Log::info('flow-manager event without flow match', [
            'event' => $this->event,
            'payload' => $this->payload,
        ]);
    }

    private function updateFlowStatus(Flow $flow): void
    {
        $status = $this->payload['new_state'] ?? $this->payload['status'] ?? null;

        if ($this->event === 'container_crashed') {
            $flow->update([
                'status' => 'error',
                'last_finished_at' => now(),
            ]);
            $flow->runs()
                ->whereNull('finished_at')
                ->latest()
                ->first()?->update([
                    'status' => 'error',
                    'finished_at' => now(),
                    'meta' => $this->payload,
                ]);

            return;
        }

        if (! $status) {
            return;
        }

        if ($status === 'running') {
            $flow->update([
                'status' => 'running',
                'last_started_at' => now(),
            ]);
            $flow->runs()
                ->whereNull('finished_at')
                ->latest()
                ->first()?->update([
                    'status' => 'running',
                    'started_at' => now(),
                    'meta' => $this->payload,
                ]);

            return;
        }

        if (in_array($status, ['stopped', 'exited', 'finished', 'dead'], true)) {
            $flow->update([
                'status' => 'stopped',
                'last_finished_at' => now(),
            ]);
            $flow->runs()
                ->whereNull('finished_at')
                ->latest()
                ->first()?->update([
                    'status' => 'stopped',
                    'finished_at' => now(),
                    'meta' => $this->payload,
                ]);
        }
    }

    private function recordLog(Flow $flow): void
    {
        $level = match ($this->event) {
            'container_health_warning', 'resource_alert' => 'warning',
            'container_crashed' => 'error',
            default => 'info',
        };

        FlowLog::create([
            'flow_id' => $flow->id,
            'flow_run_id' => $flow->runs()->latest()->value('id'),
            'level' => $level,
            'message' => sprintf('Event: %s', $this->event),
            'context' => $this->payload,
        ]);
    }
}
