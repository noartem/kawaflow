<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class FlowLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'flow_id',
        'flow_run_id',
        'node_key',
        'level',
        'message',
        'context',
    ];

    protected $casts = [
        'context' => 'array',
    ];

    public function flow(): BelongsTo
    {
        return $this->belongsTo(Flow::class);
    }

    public function run(): BelongsTo
    {
        return $this->belongsTo(FlowRun::class, 'flow_run_id');
    }
}
