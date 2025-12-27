<?php

namespace App\Http\Controllers;

use App\Models\Flow;
use App\Models\FlowHistory;
use App\Services\FlowService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use Inertia\Inertia;
use Inertia\Response;

class FlowController extends Controller
{
    private const DEFAULT_CODE = <<<PY
from kawa import actor, event, NotSupportedEvent, Context
from kawa.cron import CronEvent


@actor(receivs=CronEvent.by("0 8 * * *"))
def MorningActor(ctx: Context, event):
    print("Good morning!")
PY;

    public function index(Request $request): Response
    {
        $query = Flow::query()
            ->withCount('runs')
            ->forUser($request->user())
            ->latest();

        return Inertia::render('flows/Index', [
            'flows' => $query->get(),
        ]);
    }

    public function create(Request $request): Response
    {
        $user = $request->user();

        return Inertia::render('flows/Editor', [
            'mode' => 'create',
            'flow' => [
                'id' => null,
                'name' => __('flows.default_name'),
                'slug' => null,
                'description' => '',
                'code' => self::DEFAULT_CODE,
                'graph' => $this->defaultGraph(),
                'status' => 'draft',
                'runs_count' => 0,
                'last_started_at' => null,
                'last_finished_at' => null,
                'user' => [
                    'name' => $user?->name,
                ],
            ],
            'productionRun' => null,
            'developmentRun' => null,
            'productionRuns' => [],
            'developmentRuns' => [],
            'productionLogs' => [],
            'developmentLogs' => [],
            'status' => null,
            'runStats' => [],
            'history' => [],
            'permissions' => [
                'canRun' => false,
                'canUpdate' => $request->user()->can('create', Flow::class),
                'canDelete' => false,
            ],
            'viewMode' => 'development',
            'requiresDeletePassword' => false,
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'description' => ['nullable', 'string', 'max:1000'],
            'code' => ['nullable', 'string'],
            'graph' => ['nullable', 'array'],
        ]);

        $slug = Str::slug($data['name']) ?: Str::random(8);
        $suffix = 1;
        while (Flow::where('slug', $slug)->exists()) {
            $slug = Str::slug($data['name']).'-'.$suffix;
            $suffix++;
        }

        $flow = Flow::create([
            ...$data,
            'user_id' => $request->user()->id,
            'status' => 'draft',
            'slug' => $slug,
        ]);

        return redirect()->route('flows.show', $flow)->with('success', __('flows.created'));
    }

    public function show(Request $request, Flow $flow, FlowService $flows): Response
    {
        $flow->load('user')->loadCount('runs');

        $productionRun = $flow->activeRun('production');
        $developmentRun = $flow->activeRun('development');
        $productionRuns = $flow->runs()->where('type', 'production')->latest()->limit(6)->get();
        $developmentRuns = $flow->runs()->where('type', 'development')->latest()->limit(6)->get();
        $productionLogs = $productionRun?->logs()->latest()->limit(50)->get() ?? collect();
        $developmentLogs = $developmentRun?->logs()->latest()->limit(50)->get() ?? collect();
        $history = $flow->histories()->latest()->limit(10)->get();
        $viewMode = $request->user()->can('update', $flow) ? 'development' : 'production';

        return Inertia::render('flows/Editor', [
            'mode' => 'edit',
            'flow' => $flow,
            'productionRun' => $productionRun,
            'developmentRun' => $developmentRun,
            'productionRuns' => $productionRuns,
            'developmentRuns' => $developmentRuns,
            'productionLogs' => $productionLogs,
            'developmentLogs' => $developmentLogs,
            'status' => $flow->status,
            'runStats' => $this->runStats($flow),
            'history' => $history,
            'permissions' => [
                'canRun' => $request->user()->can('run', $flow),
                'canUpdate' => $request->user()->can('update', $flow),
                'canDelete' => $request->user()->can('delete', $flow),
            ],
            'viewMode' => $viewMode,
            'requiresDeletePassword' => $flow->hadProductionDeploy(),
        ]);
    }

    public function update(Request $request, Flow $flow, FlowService $flows): RedirectResponse
    {
        $data = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'description' => ['nullable', 'string', 'max:1000'],
            'code' => ['nullable', 'string'],
            'graph' => ['nullable', 'array'],
        ]);

        if (array_key_exists('code', $data) && ($flow->code ?? '') !== ($data['code'] ?? '')) {
            FlowHistory::create([
                'flow_id' => $flow->id,
                'code' => $flow->code ?? '',
                'diff' => $this->buildDiff($flow->code ?? '', $data['code'] ?? ''),
            ]);
        }

        $flow->update($data);

        return redirect()->route('flows.show', $flow)->with('success', __('flows.updated'));
    }

    public function destroy(Request $request, Flow $flow, FlowService $flows): RedirectResponse
    {
        if ($flow->hasActiveDeploys()) {
            return redirect()
                ->route('flows.show', $flow)
                ->with('error', __('flows.delete.error_active'));
        }

        if ($flow->hadProductionDeploy()) {
            $request->validate([
                'password' => ['required', 'string'],
            ]);

            if (! Hash::check((string) $request->input('password'), (string) $request->user()->password)) {
                return redirect()
                    ->route('flows.show', $flow)
                    ->with('error', __('flows.delete.error_password'));
            }
        }

        $flows->delete($flow);
        $flow->delete();

        return redirect()->route('flows.index')->with('success', __('flows.deleted'));
    }

    /**
     * @return array{nodes: array<int, mixed>, edges: array<int, mixed>}
     */
    private function defaultGraph(): array
    {
        return [
            'nodes' => [],
            'edges' => [],
        ];
    }

    /**
     * @return array<int, array{status: string, total: int}>
     */
    private function runStats(Flow $flow): array
    {
        return $flow->runs()
            ->selectRaw('status, count(*) as total')
            ->groupBy('status')
            ->get()
            ->map(static fn ($row) => [
                'status' => $row->status ?? 'unknown',
                'total' => (int) $row->total,
            ])
            ->values()
            ->all();
    }

    private function buildDiff(string $from, string $to): string
    {
        if (function_exists('xdiff_string_diff')) {
            $diff = xdiff_string_diff($from, $to, 1);
            if (is_string($diff)) {
                return $diff;
            }
        }

        $fromLines = preg_split('/\R/', $from) ?: [];
        $toLines = preg_split('/\R/', $to) ?: [];
        $fromCount = count($fromLines);
        $toCount = count($toLines);

        $dp = array_fill(0, $fromCount + 1, array_fill(0, $toCount + 1, 0));
        for ($i = $fromCount - 1; $i >= 0; $i--) {
            for ($j = $toCount - 1; $j >= 0; $j--) {
                if ($fromLines[$i] === $toLines[$j]) {
                    $dp[$i][$j] = $dp[$i + 1][$j + 1] + 1;
                } else {
                    $dp[$i][$j] = max($dp[$i + 1][$j], $dp[$i][$j + 1]);
                }
            }
        }

        $diff = [];
        $i = 0;
        $j = 0;
        while ($i < $fromCount && $j < $toCount) {
            if ($fromLines[$i] === $toLines[$j]) {
                $diff[] = ' '.$fromLines[$i];
                $i++;
                $j++;
            } elseif ($dp[$i + 1][$j] >= $dp[$i][$j + 1]) {
                $diff[] = '-'.$fromLines[$i];
                $i++;
            } else {
                $diff[] = '+'.$toLines[$j];
                $j++;
            }
        }

        while ($i < $fromCount) {
            $diff[] = '-'.$fromLines[$i];
            $i++;
        }

        while ($j < $toCount) {
            $diff[] = '+'.$toLines[$j];
            $j++;
        }

        return implode("\n", $diff);
    }
}
