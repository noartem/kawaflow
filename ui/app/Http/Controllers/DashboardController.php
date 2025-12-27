<?php

namespace App\Http\Controllers;

use App\Models\Flow;
use App\Models\FlowRun;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    public function __invoke(Request $request): Response
    {
        $user = $request->user();

        $flowQuery = Flow::query()->forUser($user);
        $flowIds = (clone $flowQuery)->pluck('id');

        $flowStats = [
            'total' => $flowIds->count(),
            'running' => (clone $flowQuery)->where('status', 'running')->count(),
            'stopped' => (clone $flowQuery)->where('status', 'stopped')->count(),
            'errors' => (clone $flowQuery)->where('status', 'error')->count(),
            'withContainer' => (clone $flowQuery)->whereNotNull('container_id')->count(),
            'lastUpdatedAt' => (clone $flowQuery)->max('updated_at'),
        ];

        $recentFlows = (clone $flowQuery)
            ->withCount('runs')
            ->latest('updated_at')
            ->limit(6)
            ->get([
                'id',
                'name',
                'slug',
                'status',
                'last_started_at',
                'last_finished_at',
                'updated_at',
            ]);

        $runsByStatus = FlowRun::query()
            ->selectRaw('status, count(*) as total')
            ->whereIn('flow_id', $flowIds)
            ->groupBy('status')
            ->get()
            ->map(static fn ($row) => [
                'status' => $row->status ?? 'unknown',
                'total' => (int) $row->total,
            ])
            ->values();

        $recentRuns = FlowRun::query()
            ->with('flow:id,name,slug,status')
            ->whereIn('flow_id', $flowIds)
            ->latest()
            ->limit(8)
            ->get([
                'id',
                'flow_id',
                'type',
                'active',
                'status',
                'started_at',
                'finished_at',
                'created_at',
            ]);

        $activeDeploys = FlowRun::query()
            ->with('flow:id,name,slug,status')
            ->whereIn('flow_id', $flowIds)
            ->where('active', true)
            ->latest('started_at')
            ->limit(10)
            ->get([
                'id',
                'flow_id',
                'type',
                'active',
                'status',
                'started_at',
                'finished_at',
                'created_at',
            ]);

        return Inertia::render('Dashboard', [
            'flowStats' => [
                ...$flowStats,
                'runsByStatus' => $runsByStatus,
            ],
            'recentFlows' => $recentFlows,
            'recentRuns' => $recentRuns,
            'activeDeploys' => $activeDeploys,
        ]);
    }
}
