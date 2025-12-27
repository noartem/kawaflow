<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('flows', static function (Blueprint $table) {
            $table->timestamp('archived_at')->nullable()->index();
        });

        Schema::table('flow_runs', static function (Blueprint $table) {
            $table->string('type')->default('development')->index();
            $table->boolean('active')->default(true)->index();
            $table->text('lock')->nullable();
            $table->json('actors')->nullable();
            $table->json('events')->nullable();
        });

        Schema::create('flow_histories', static function (Blueprint $table) {
            $table->id();
            $table->foreignId('flow_id')->constrained()->cascadeOnDelete();
            $table->text('code');
            $table->text('diff')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('flow_histories');

        Schema::table('flow_runs', static function (Blueprint $table) {
            $table->dropColumn(['type', 'active', 'lock', 'actors', 'events']);
        });

        Schema::table('flows', static function (Blueprint $table) {
            $table->dropColumn('archived_at');
        });
    }
};
