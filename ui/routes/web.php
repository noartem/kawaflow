<?php

use App\Http\Controllers\FlowActionController;
use App\Http\Controllers\FlowController;
use App\Http\Controllers\FlowLogController;
use App\Http\Controllers\DashboardController;
use App\Models\Flow;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;
use Laravel\Fortify\Features as FortifyFeatures;

Route::get('/', static function () {
    return Inertia::render('Welcome', [
        'canRegister' => FortifyFeatures::enabled(FortifyFeatures::registration()),
    ]);
})->name('home');

Route::get('dashboard', DashboardController::class)
    ->middleware(['auth', 'verified'])
    ->name('dashboard');

Route::middleware('auth')->group(function () {
    Route::get('flows', [FlowController::class, 'index'])->name('flows.index')->can('view-any', Flow::class);
    Route::get('flows/create', [FlowController::class, 'create'])->name('flows.create')->can('create', Flow::class);
    Route::post('flows', [FlowController::class, 'store'])->name('flows.store')->can('create', Flow::class);
    Route::get('flows/{flow}', [FlowController::class, 'show'])->name('flows.show')->can('update', [Flow::class, 'flow']);
    Route::put('flows/{flow}', [FlowController::class, 'update'])->name('flows.update')->can('view-any', [Flow::class, 'flow']);
    Route::delete('flows/{flow}', [FlowController::class, 'destroy'])->name('flows.destroy')->can('view-any', [Flow::class, 'flow']);
    Route::post('flows/{flow}/run', [FlowActionController::class, 'run'])->name('flows.run')->can('run', [Flow::class, 'flow']);
    Route::post('flows/{flow}/stop', [FlowActionController::class, 'stop'])->name('flows.stop')->can('run', [Flow::class, 'flow']);
    Route::get('flows/{flow}/logs', [FlowLogController::class, 'index'])->name('flows.logs')->can('view-logs', [Flow::class, 'flow']);
});


require __DIR__ . '/settings.php';
