<?php

namespace App\Services;

use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use PhpAmqpLib\Channel\AMQPChannel;
use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;
use Throwable;

class FlowManagerClient
{
    private ?AMQPStreamConnection $connection = null;

    private ?AMQPChannel $channel = null;

    public function __construct(
        private readonly ?string $rabbitUrl = null,
        private readonly ?string $commandQueue = null,
        private readonly ?string $responseQueue = null,
        private readonly ?string $eventExchange = null,
        private readonly ?int $timeoutMs = null,
    ) {
    }

    public function __destruct()
    {
        $this->close();
    }

    public function health(): array
    {
        try {
            $this->connect();

            return ['ok' => true, 'message' => 'RabbitMQ connection established'];
        } catch (Throwable $exception) {
            Log::error('flow-manager health failed', [
                'exception' => $exception->getMessage(),
            ]);

            return ['ok' => false, 'message' => $exception->getMessage()];
        }
    }

    public function createContainer(array $payload): array
    {
        return $this->run('create_container', $payload);
    }

    public function startContainer(string $containerId): array
    {
        return $this->run('start_container', ['container_id' => $containerId]);
    }

    public function stopContainer(string $containerId): array
    {
        return $this->run('stop_container', ['container_id' => $containerId]);
    }

    public function deleteContainer(string $containerId): array
    {
        return $this->run('delete_container', ['container_id' => $containerId]);
    }

    public function status(string $containerId): array
    {
        return $this->run('get_container_status', ['container_id' => $containerId]);
    }

    public function listContainers(): array
    {
        return $this->run('list_containers');
    }

    protected function run(string $action, array $payload = []): array
    {
        try {
            $this->connect();

            $correlationId = (string) Str::uuid();

            $messagePayload = [
                'action' => $action,
                'data' => $payload,
                'correlation_id' => $correlationId,
            ];

            $message = new AMQPMessage(
                json_encode($messagePayload, JSON_THROW_ON_ERROR),
                [
                    'content_type' => 'application/json',
                    'delivery_mode' => 2,
                    'correlation_id' => $correlationId,
                ],
            );

            $this->channel?->basic_publish(
                $message,
                $this->eventExchangeName(),
                'command.'.$action,
            );

            return [
                'ok' => true,
                'message' => 'Command published to RabbitMQ',
                'correlation_id' => $correlationId,
            ];
        } catch (Throwable $exception) {
            Log::error('flow-manager command failed', [
                'action' => $action,
                'payload' => $payload,
                'exception' => $exception->getMessage(),
            ]);

            return [
                'ok' => false,
                'message' => $exception->getMessage(),
            ];
        }
    }

    private function connect(): void
    {
        if ($this->connection?->isConnected() && $this->channel !== null) {
            return;
        }

        $config = $this->parseRabbitUrl(
            $this->rabbitUrl ?? (string) config('services.flow_manager.rabbitmq_url')
        );

        $this->connection = new AMQPStreamConnection(
            $config['host'],
            $config['port'],
            $config['user'],
            $config['password'],
            $config['vhost'],
            connection_timeout: $this->timeoutSeconds(),
            read_write_timeout: $this->timeoutSeconds(),
            heartbeat: 0.0,
            channel_rpc_timeout: $this->timeoutSeconds(),
        );

        $this->channel = $this->connection->channel();
        $this->setupTopology();
    }

    private function setupTopology(): void
    {
        if (! $this->channel) {
            return;
        }

        $exchange = $this->eventExchangeName();
        $commandQueue = $this->commandQueueName();

        $this->channel->exchange_declare($exchange, 'topic', false, true, false);
        $this->channel->queue_declare($commandQueue, false, true, false, false);
        $this->channel->queue_bind($commandQueue, $exchange, 'command.*');
    }

    private function parseRabbitUrl(string $url): array
    {
        $parts = parse_url($url) ?: [];

        return [
            'host' => $parts['host'] ?? 'rabbitmq',
            'port' => (int) ($parts['port'] ?? 5672),
            'user' => $parts['user'] ?? 'guest',
            'password' => $parts['pass'] ?? 'guest',
            'vhost' => isset($parts['path']) && $parts['path'] !== '/'
                ? ltrim($parts['path'], '/')
                : '/',
        ];
    }

    private function timeoutSeconds(): float
    {
        return ($this->timeoutMs ?? (int) config('services.flow_manager.timeout', 8000)) / 1000;
    }

    private function eventExchangeName(): string
    {
        return $this->eventExchange ?? (string) config('services.flow_manager.event_exchange', 'flow-manager.events');
    }

    private function commandQueueName(): string
    {
        return $this->commandQueue ?? (string) config('services.flow_manager.command_queue', 'flow-manager.commands');
    }

    private function responseQueueName(): ?string
    {
        return $this->responseQueue ? (string) $this->responseQueue : null;
    }

    private function close(): void
    {
        $this->channel?->close();
        $this->connection?->close();
    }
}
