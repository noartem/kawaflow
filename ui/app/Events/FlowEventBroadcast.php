<?php

namespace App\Events;

use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\ShouldBroadcastNow;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class FlowEventBroadcast implements ShouldBroadcastNow
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public function __construct(
        public readonly int $flowId,
        public readonly string $event,
        public readonly array $payload = [],
    ) {
    }

    public function broadcastOn(): array
    {
        return [new Channel('flows')];
    }

    public function broadcastAs(): string
    {
        return 'flow-manager.'.$this->event;
    }

    public function broadcastWith(): array
    {
        return [
            'flow_id' => $this->flowId,
            'event' => $this->event,
            'payload' => $this->payload,
        ];
    }
}
