<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class FlowRun extends Model
{
    protected $fillable = [
        'flow_id',
        'status',
        'container_id',
        'meta',
        'started_at',
        'finished_at',
    ];

    protected $casts = [
        'meta' => 'array',
        'started_at' => 'datetime',
        'finished_at' => 'datetime',
    ];

    public function flow(): BelongsTo
    {
        return $this->belongsTo(Flow::class);
    }

    public function logs(): HasMany
    {
        return $this->hasMany(FlowLog::class);
    }
}
