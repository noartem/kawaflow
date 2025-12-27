<?php

namespace App\Http\Controllers\Settings;

use App\Http\Requests\Settings\LocaleUpdateRequest;
use Illuminate\Http\RedirectResponse;

class LocaleController
{
    public function update(LocaleUpdateRequest $request): RedirectResponse
    {
        $locale = $request->validated('locale');

        if ($request->user()) {
            $request->user()->update(['locale' => $locale]);
        }

        app()->setLocale($locale);

        return back()
            ->with('success', __('settings.language.updated'))
            ->withCookie(cookie('locale', $locale, 60 * 24 * 365));
    }
}
