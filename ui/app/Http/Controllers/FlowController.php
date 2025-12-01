<?php

namespace App\Http\Controllers;

use App\Models\Flow;
use App\Services\FlowService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
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
                'name' => 'Новый flow',
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
            'runs' => [],
            'logs' => [],
            'status' => null,
            'runStats' => [],
            'permissions' => [
                'canRun' => false,
                'canUpdate' => $request->user()->can('create', Flow::class),
                'canDelete' => false,
            ],
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

        return redirect()->route('flows.show', $flow)->with('success', 'Flow создан.');
    }

    public function show(Request $request, Flow $flow, FlowService $flows): Response
    {
        $flow->load('user')->loadCount('runs');

        $runs = $flow->runs()->latest()->limit(6)->get();
        $logs = $flow->logs()->latest()->limit(50)->get();

        return Inertia::render('flows/Editor', [
            'mode' => 'edit',
            'flow' => $flow,
            'runs' => $runs,
            'logs' => $logs,
            'status' => $flow->status,
            'runStats' => $this->runStats($flow),
            'permissions' => [
                'canRun' => $request->user()->can('run', $flow),
                'canUpdate' => $request->user()->can('update', $flow),
                'canDelete' => $request->user()->can('delete', $flow),
            ],
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

        $flow->update($data);

        return redirect()->route('flows.show', $flow)->with('success', 'Flow обновлен.');
    }

    public function destroy(Flow $flow, FlowService $flows): RedirectResponse
    {
        $flows->delete($flow);
        $flow->delete();

        return redirect()->route('flows.index')->with('success', 'Flow удален.');
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
}
