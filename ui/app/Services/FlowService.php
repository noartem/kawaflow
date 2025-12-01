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
