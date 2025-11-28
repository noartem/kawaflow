<?php

namespace Database\Seeders;

use App\Enums\Role;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        User::factory()->admin()->create([
            'name' => 'Admin',
            'email' => env('ADMIN_EMAIL', 'admin@kawaflow.local'),
            'password' => Hash::make(env('ADMIN_PASSWORD', 'admin1234')),
            'role' => Role::ADMIN,
        ]);

        User::factory()->create([
            'name' => 'Demo User',
            'email' => 'user@kawaflow.local',
            'password' => Hash::make('password123'),
            'role' => Role::USER,
        ]);
    }
}
