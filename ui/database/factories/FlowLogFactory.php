<?php

namespace Database\Factories;

use App\Models\Flow;
use App\Models\FlowLog;
use App\Models\FlowRun;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

/**
 * @extends Factory<FlowLog>
 */
class FlowLogFactory extends Factory
{
    protected $model = FlowLog::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'flow_id' => Flow::factory(),
            'flow_run_id' => null,
            'node_key' => fake()->optional()->randomElement(['source', 'worker', 'sink']),
            'level' => fake()->randomElement(['info', 'debug', 'warning', 'error']),
            'message' => fake()->sentence(10),
            'context' => [
                'trace_id' => Str::uuid()->toString(),
                'payload' => fake()->randomElement(['sync', 'ingest', 'cleanup']),
            ],
        ];
    }

    public function forFlow(Flow $flow): static
    {
        return $this->state(fn () => [
            'flow_id' => $flow->id,
        ]);
    }

    public function forRun(FlowRun $run): static
    {
        return $this->state(fn () => [
            'flow_id' => $run->flow_id,
            'flow_run_id' => $run->id,
        ]);
    }
}
