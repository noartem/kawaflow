<?php

namespace App\Enums;

enum Role: string
{
    case ADMIN = 'admin';
    case USER = 'user';

    /**
     * @return list<Permission>
     */
    public function permissions(): array
    {
        return match ($this) {
            self::ADMIN => [
                Permission::VIEW_FLOWS,
                Permission::VIEW_ALL_FLOWS,
                Permission::MANAGE_FLOWS,
                Permission::MANAGE_OWN_FLOWS,
                Permission::RUN_FLOW,
                Permission::RUN_OWN_FLOW,
                Permission::VIEW_FLOW_LOGS,
                Permission::VIEW_OWN_FLOW_LOGS,
            ],
            self::USER => [
                Permission::VIEW_FLOWS,
                Permission::MANAGE_OWN_FLOWS,
                Permission::RUN_OWN_FLOW,
                Permission::VIEW_OWN_FLOW_LOGS,
            ],
        };
    }
}
