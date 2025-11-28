<?php

namespace App\Http\Controllers;

use App\Models\Flow;
use App\Services\FlowService;
use Illuminate\Http\RedirectResponse;

class FlowActionController extends Controller
{
    public function run(Flow $flow, FlowService $flows): RedirectResponse
    {
        $result = $flows->start($flow);

        return redirect()
            ->route('flows.show', $flow)
            ->with($result['ok'] ? 'success' : 'error', $result['ok'] ? 'Поток запущен' : 'Не удалось запустить поток');
    }

    public function stop(Flow $flow, FlowService $flows): RedirectResponse
    {
        $result = $flows->stop($flow);

        return redirect()
            ->route('flows.show', $flow)
            ->with($result['ok'] ? 'success' : 'error', $result['ok'] ? 'Поток остановлен' : 'Не удалось остановить поток');
    }
}
