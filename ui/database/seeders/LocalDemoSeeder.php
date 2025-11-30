<?php

namespace Database\Seeders;

use App\Models\Flow;
use App\Models\FlowLog;
use App\Models\FlowRun;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Collection;
use Illuminate\Support\Str;
use Spatie\Permission\PermissionRegistrar;

class LocalDemoSeeder extends Seeder
{
    public function run(): void
    {
        if (! app()->environment(['local', 'dev'])) {
            return;
        }

        $this->callOnce(RolesAndPermissionsSeeder::class);
        app(PermissionRegistrar::class)->forgetCachedPermissions();

        if (Flow::query()->exists()) {
            return;
        }

        $admin = User::factory()->admin()->create([
            'name' => 'Demo Admin',
            'email' => 'demo.admin@kawaflow.localhost',
        ]);

        $members = User::factory()
            ->count(5)
            ->withoutTwoFactor()
            ->create();

        $members->push($admin);

        $members->each(fn (User $user) => $this->seedFlowsFor($user));
    }

    private function seedFlowsFor(User $user): void
    {
        $flows = Flow::factory()
            ->for($user)
            ->count(fake()->numberBetween(2, 4))
            ->create();

        foreach ($flows as $flow) {
            $runs = FlowRun::factory()
                ->forFlow($flow)
                ->count(fake()->numberBetween(1, 5))
                ->create();

            foreach ($runs as $run) {
                FlowLog::factory()->forRun($run)->count(fake()->numberBetween(3, 8))->create();
            }

            FlowLog::factory()->forFlow($flow)->count(fake()->numberBetween(2, 4))->create();

            $flow->update([
                'status' => $this->flowStatus($runs),
                'last_started_at' => $runs->max('started_at'),
                'last_finished_at' => $runs->max('finished_at'),
                'container_id' => $flow->container_id ?? 'flow-'.Str::lower(Str::random(8)),
            ]);
        }
    }

    private function flowStatus(Collection $runs): string
    {
        if ($runs->contains(fn (FlowRun $run) => $run->status === 'running')) {
            return 'running';
        }

        if ($runs->contains(fn (FlowRun $run) => $run->status === 'failed')) {
            return 'error';
        }

        return $runs->isEmpty() ? 'draft' : 'stopped';
    }
}
