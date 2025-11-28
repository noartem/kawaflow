<?php

namespace App\Services;

use App\Models\Flow;
use App\Models\FlowRun;
use App\Services\FlowManagerClient;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Log;

final readonly class FlowService
{
    public function __construct(
        private FlowManagerClient $client,
    ) {
    }

    public function getStatus(Flow $flow): string
    {
        // TODO: add realization
        throw new \RuntimeException('missing realization');
    }

    public function persistCode(Flow $flow): string
    {
        $basePath = rtrim(config('flows.storage_path', storage_path('flows')), '/');
        $targetDir = $basePath.'/'.$flow->slug;
        $entrypoint = $flow->entrypoint ?: 'main.py';

        File::ensureDirectoryExists($targetDir);
        File::put($targetDir.'/'.$entrypoint, $flow->code ?? '# your flow goes here');

        return $targetDir;
    }

    public function start(Flow $flow): array
    {
        // TODO: add realization
        throw new \RuntimeException('missing realization');
    }

    public function stop(Flow $flow): array
    {
        // TODO: add realization
        throw new \RuntimeException('missing realization');
    }

    public function delete(Flow $flow): array
    {
        // TODO: add realization
        throw new \RuntimeException('missing realization');
    }
}
