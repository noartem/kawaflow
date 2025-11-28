<?php

namespace App\Policies;

use App\Enums\Permission;
use App\Models\Flow;
use App\Models\User;

class FlowPolicy
{
    public function viewAny(User $user): bool
    {
        return $user->hasPermission(Permission::VIEW_ALL_FLOWS)
            || $user->hasPermission(Permission::VIEW_FLOWS);
    }

    public function viewAll(User $user): bool
    {
        return $user->hasPermission(Permission::VIEW_ALL_FLOWS);
    }

    public function view(User $user, Flow $flow): bool
    {
        if ($user->hasPermission(Permission::VIEW_ALL_FLOWS)) {
            return true;
        }

        return $user->hasPermission(Permission::VIEW_FLOWS)
            && $flow->user_id === $user->id;
    }

    public function create(User $user): bool
    {
        return $user->hasPermission(Permission::MANAGE_FLOWS)
            || $user->hasPermission(Permission::MANAGE_OWN_FLOWS);
    }

    public function update(User $user, Flow $flow): bool
    {
        if ($user->hasPermission(Permission::MANAGE_FLOWS)) {
            return true;
        }

        return $user->hasPermission(Permission::MANAGE_OWN_FLOWS)
            && $flow->user_id === $user->id;
    }

    public function delete(User $user, Flow $flow): bool
    {
        if ($user->hasPermission(Permission::MANAGE_FLOWS)) {
            return true;
        }

        return $user->hasPermission(Permission::MANAGE_OWN_FLOWS)
            && $flow->user_id === $user->id;
    }

    public function run(User $user, Flow $flow): bool
    {
        if ($user->hasPermission(Permission::RUN_FLOW)) {
            return true;
        }

        return $user->hasPermission(Permission::RUN_OWN_FLOW)
            && $flow->user_id === $user->id;
    }

    public function viewLogs(User $user, Flow $flow): bool
    {
        if ($user->hasPermission(Permission::VIEW_FLOW_LOGS)) {
            return true;
        }

        return $user->hasPermission(Permission::VIEW_OWN_FLOW_LOGS)
            && $flow->user_id === $user->id;
    }
}
