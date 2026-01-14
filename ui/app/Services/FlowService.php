<?php

namespace App\Services;

use App\Models\Flow;
use App\Models\FlowRun;
use App\Services\FlowManagerClient;
use Illuminate\Support\Facades\File;

final readonly class FlowService
{
    public function __construct(
        private FlowManagerClient $client,
    ) {
    }

    public function getStatus(Flow $flow): string
    {
        $productionRun = $flow->activeRun('production');
        if ($productionRun) {
            return $productionRun->status ?? 'unknown';
        }

        return $flow->status ?? 'draft';
    }

    public function start(Flow $flow): array
    {
        return $this->deployDevelopment($flow);
    }

    public function stop(Flow $flow): array
    {
        return $this->stopDeployment($flow, 'development');
    }

    public function delete(Flow $flow): array
    {
        $activeRuns = $flow->runs()->where('active', true)->get();
        foreach ($activeRuns as $run) {
            $this->stopDeployment($flow, $run->type);
        }

        return ['ok' => true];
    }

    public function deployProduction(Flow $flow): array
    {
        $run = $this->createDeployment($flow, 'production', 'locking');

        $this->client->generateLock([
            'flow_id' => $flow->id,
            'flow_run_id' => $run->id,
            'image' => $flow->image,
            'code' => $flow->code ?? '',
        ]);

        return ['ok' => true, 'run_id' => $run->id];
    }

    public function undeployProduction(Flow $flow): array
    {
        return $this->stopDeployment($flow, 'production');
    }

    public function markLockReady(Flow $flow, FlowRun $run): void
    {
        if ($run->type !== 'production') {
            return;
        }

        $this->writeDeploymentFiles($flow, $run);
        $run->update([
            'status' => 'ready',
        ]);
    }

    private function deployDevelopment(Flow $flow): array
    {
        $run = $this->createDeployment($flow, 'development', 'running');
        $payload = [
            'image' => $flow->image ?? 'flow:dev',
            'name' => sprintf('flow-%d-run-%d', $flow->id, $run->id),
            'flow_id' => $flow->id,
            'flow_run_id' => $run->id,
            'flow_name' => $flow->name,
            'graph_hash' => $this->graphHash($flow),
            'test_run_id' => (string) config('services.flow_manager.test_run_id'),
            'labels' => [
                'kawaflow.flow_id' => (string) $flow->id,
                'kawaflow.flow_run_id' => (string) $run->id,
                'kawaflow.flow_name' => $flow->name,
                'kawaflow.graph_hash' => $this->graphHash($flow),
            ],
            'environment' => [
                'FLOW_ID' => (string) $flow->id,
                'FLOW_RUN_ID' => (string) $run->id,
            ],
            'command' => [
                '/bin/sh',
                '-c',
                sprintf(
                    'echo "kawaflow flow %d" && tail -f /dev/null',
                    $flow->id
                ),
            ],
        ];
        if (! $payload['test_run_id']) {
            unset($payload['test_run_id']);
        }
        $this->client->createContainer($payload);

        return [
            'ok' => true,
            'run_id' => $run->id,
        ];
    }

    private function stopDeployment(Flow $flow, string $type): array
    {
        $run = $flow->activeRun($type);
        if (! $run) {
            return ['ok' => true];
        }

        $run->update([
            'active' => false,
            'status' => 'stopped',
            'finished_at' => now(),
        ]);

        if ($type === 'production' && $flow->status === 'running') {
            $flow->update([
                'status' => 'stopped',
                'last_finished_at' => now(),
            ]);
        }

        $containerId = $run->container_id ?? $flow->container_id;
        if (! $containerId) {
            $deadline = now()->addSeconds(5);
            while (! $containerId && now()->lt($deadline)) {
                usleep(200000);
                $run->refresh();
                $flow->refresh();
                $containerId = $run->container_id ?? $flow->container_id;
            }
        }
        if ($containerId) {
            $this->client->stopContainer($containerId);
        }

        return ['ok' => true];
    }

    private function createDeployment(Flow $flow, string $type, string $status): FlowRun
    {
        $flow->runs()
            ->where('type', $type)
            ->where('active', true)
            ->update([
                'active' => false,
                'finished_at' => now(),
            ]);

        $run = $flow->runs()->create([
            'type' => $type,
            'active' => true,
            'status' => $status,
            'started_at' => now(),
        ]);

        if ($type === 'development') {
            $this->writeDeploymentFiles($flow, $run);
        }

        if ($type === 'production') {
            $flow->update([
                'status' => 'deploying',
                'last_started_at' => now(),
            ]);
        }

        return $run;
    }

    private function writeDeploymentFiles(Flow $flow, FlowRun $run): void
    {
        $root = storage_path(sprintf('app/flows/%d/%s/%d', $flow->id, $run->type, $run->id));
        File::ensureDirectoryExists($root);
        File::put($root.'/main.py', $flow->code ?? '');

        if ($run->type === 'production' && $run->lock) {
            File::put($root.'/uv.lock', $run->lock);
        }
    }

    private function graphHash(Flow $flow): string
    {
        $graph = $flow->graph ?? [];
        $encodedGraph = json_encode($graph, JSON_THROW_ON_ERROR);

        return hash('sha256', ($flow->code ?? '').'::'.$encodedGraph);
    }
}
