<?php

namespace App\Enums;

enum Permission: string
{
    case VIEW_FLOWS = 'view_flows';
    case VIEW_ALL_FLOWS = 'view_all_flows';
    case MANAGE_FLOWS = 'manage_flows';
    case MANAGE_OWN_FLOWS = 'manage_own_flows';
    case RUN_FLOW = 'run_flow';
    case RUN_OWN_FLOW = 'run_own_flow';
    case VIEW_FLOW_LOGS = 'view_flow_logs';
    case VIEW_OWN_FLOW_LOGS = 'view_own_flow_logs';
}
