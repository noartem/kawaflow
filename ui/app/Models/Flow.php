<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Flow extends Model
{
    protected $fillable = [
        'user_id',
        'name',
        'slug',
        'description',
        'code',
        'graph',
        'status',
        'container_id',
        'entrypoint',
        'image',
        'last_started_at',
        'last_finished_at',
    ];

    protected $casts = [
        'graph' => 'array',
        'last_started_at' => 'datetime',
        'last_finished_at' => 'datetime',
    ];

    protected static function booted(): void
    {
        static::creating(static function (Flow $flow): void {
            if (empty($flow->slug)) {
                $flow->slug = Str::slug($flow->name) ?: Str::uuid()->toString();
            }
        });
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function runs(): HasMany
    {
        return $this->hasMany(FlowRun::class);
    }

    public function logs(): HasMany
    {
        return $this->hasMany(FlowLog::class);
    }

    public function scopeForUser(Builder $query, User $user): void {
        if ($user->can('view-all', self::class)) {
            return;
        }

        $query->where('user_id', $user->id);
    }
}
