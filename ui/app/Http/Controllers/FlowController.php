<?php

namespace App\Http\Controllers;

use App\Models\Flow;
use App\Services\FlowManagerClient;
use App\Services\FlowService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Inertia\Inertia;
use Inertia\Response;

class FlowController extends Controller
{
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

    public function store(Request $request, FlowService $flows): RedirectResponse
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

        $flows->persistCode($flow);

        return redirect()->route('flows.show', $flow)->with('success', 'Flow создан.');
    }

    public function show(Flow $flow, FlowService $flows): Response {
        return Inertia::render('flows/Show', [
            'flow' => $flow->load('user'),
            'runs' => $flow->runs()->latest()->limit(5)->get(),
            'logs' => $flow->logs()->latest()->limit(50)->get(),
            'status' => $flow->container_id
                ? $flows->getStatus($flow)
                : null,
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
        $flows->persistCode($flow);

        return redirect()->route('flows.show', $flow)->with('success', 'Flow обновлен.');
    }

    public function destroy(Flow $flow, FlowService $flows): RedirectResponse
    {
        $flows->delete($flow);
        $flow->delete();

        return redirect()->route('flows.index')->with('success', 'Flow удален.');
    }
}
