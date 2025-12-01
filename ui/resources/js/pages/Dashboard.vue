<script setup lang="ts">
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import AppLayout from '@/layouts/AppLayout.vue';
import { dashboard } from '@/routes';
import { index as flowsIndex, show as flowShow } from '@/routes/flows';
import { type BreadcrumbItem, type FlowRunSummary, type FlowSidebarItem, type FlowStatsSummary } from '@/types';
import { Head, Link } from '@inertiajs/vue3';
import { Activity, ArrowUpRight, Clock3, Plus, Workflow } from 'lucide-vue-next';
import { computed } from 'vue';

interface FlowOverview extends FlowSidebarItem {
    runs_count?: number;
    updated_at?: string;
}

const props = defineProps<{
    flowStats: FlowStatsSummary;
    recentFlows: FlowOverview[];
    recentRuns: FlowRunSummary[];
}>();

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Dashboard',
        href: dashboard().url,
    },
];

const statusTone = (status?: string | null) => {
    switch (status) {
        case 'running':
            return 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/25';
        case 'error':
            return 'bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/25';
        case 'stopped':
            return 'bg-amber-500/15 text-amber-200 ring-1 ring-amber-500/25';
        default:
            return 'bg-muted text-muted-foreground ring-1 ring-border';
    }
};

const formatDate = (value?: string | null) => {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
};

const headline = computed(() => {
    const running = props.flowStats?.running ?? 0;
    const total = props.flowStats?.total ?? 0;
    const errors = props.flowStats?.errors ?? 0;
    const highlight = running > 0
        ? `${running} активных`
        : errors > 0
            ? `${errors} требует внимания`
            : `${total} всего`;

    return `У вас ${highlight} потоков`;
});

const totalRuns = computed(() => props.flowStats?.runsByStatus?.reduce((sum, row) => sum + (row.total ?? 0), 0) ?? 0);
const activePercent = computed(() => {
    const total = props.flowStats?.total ?? 0;
    const running = props.flowStats?.running ?? 0;
    return total > 0 ? Math.round((running / total) * 100) : 0;
});
const failingPercent = computed(() => {
    const total = props.flowStats?.total ?? 0;
    const errors = props.flowStats?.errors ?? 0;
    return total > 0 ? Math.round((errors / total) * 100) : 0;
});
</script>

<template>
    <Head title="Dashboard" />

    <AppLayout :breadcrumbs="breadcrumbs">
        <div class="space-y-6 px-4 pb-10 pt-2">
            <div
                class="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-primary/10 via-background to-background p-6 shadow-sm"
            >
                <div class="absolute inset-0 bg-[radial-gradient(circle_at_top,theme(colors.primary/10),transparent_35%)]" />
                <div class="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div class="space-y-3">
                        <h1 class="text-3xl font-semibold leading-tight">Панель потоков</h1>
                        <div class="flex flex-wrap gap-3 pt-2">
                            <Button as-child>
                                <Link :href="flowsIndex().url">
                                    <Plus class="size-4" />
                                    Новый поток
                                </Link>
                            </Button>
                            <Button variant="outline" as-child>
                                <Link :href="flowsIndex().url">
                                    <Workflow class="size-4" />
                                    Все потоки
                                </Link>
                            </Button>
                        </div>
                    </div>

                    <div class="flex flex-col gap-3 rounded-xl border border-border/60 bg-background/70 p-4 text-sm backdrop-blur">
                        <div class="flex items-center gap-3">
                            <div class="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">Всего</div>
                            <div class="text-3xl font-semibold">{{ flowStats?.total ?? 0 }}</div>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                            <div class="flex items-center gap-2">
                                <span class="h-2 w-2 rounded-full bg-emerald-400/70" />
                                {{ flowStats?.running ?? 0 }} running
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="h-2 w-2 rounded-full bg-amber-400/70" />
                                {{ flowStats?.stopped ?? 0 }} stopped
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="h-2 w-2 rounded-full bg-rose-400/70" />
                                {{ flowStats?.errors ?? 0 }} errors
                            </div>
                        </div>
                        <p class="text-[11px] text-muted-foreground">
                            Последнее обновление: {{ formatDate(flowStats?.lastUpdatedAt) }}
                        </p>
                    </div>
                </div>
            </div>

            <div class="grid gap-4 lg:grid-cols-3">
                <Card class="lg:col-span-2">
                    <CardHeader class="pb-3">
                        <CardTitle>Последние потоки</CardTitle>
                        <CardDescription>Свежие изменения и статус</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div v-if="recentFlows?.length" class="divide-y divide-border">
                            <div
                                v-for="flow in recentFlows"
                                :key="flow.id"
                                class="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between"
                            >
                                <div class="space-y-1">
                                    <Link
                                        :href="flowShow({ flow: flow.id }).url"
                                        class="inline-flex items-center gap-2 text-base font-semibold hover:text-primary"
                                    >
                                        <Workflow class="size-4 text-muted-foreground" />
                                        {{ flow.name }}
                                        <ArrowUpRight class="size-4" />
                                    </Link>
                                    <p class="text-sm text-muted-foreground">
                                        Запусков: {{ flow.runs_count ?? 0 }} • Обновлено {{ formatDate(flow.updated_at) }}
                                    </p>
                                </div>
                                <div class="flex items-center gap-3">
                                    <Badge :class="statusTone(flow.status)" variant="outline">
                                        {{ flow.status ?? 'draft' }}
                                    </Badge>
                                    <Link
                                        :href="flowShow({ flow: flow.id }).url"
                                        class="text-xs font-semibold text-primary hover:underline"
                                    >
                                        Открыть
                                    </Link>
                                </div>
                            </div>
                        </div>
                        <div v-else class="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
                            Пока нет потоков для отображения. Создайте первый и запустите его.
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Распределение статусов</CardTitle>
                        <CardDescription>Быстрый срез по FlowRun</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3">
                        <div
                            v-if="flowStats?.runsByStatus?.length"
                            class="space-y-3"
                        >
                            <div
                                v-for="row in flowStats.runsByStatus"
                                :key="row.status ?? 'unknown'"
                                class="space-y-1"
                            >
                                <div class="flex items-center justify-between text-sm">
                                    <div class="flex items-center gap-2">
                                        <span class="h-2 w-2 rounded-full bg-primary" />
                                        <span class="capitalize text-muted-foreground">{{ row.status ?? 'unknown' }}</span>
                                    </div>
                                    <span class="font-semibold">{{ row.total }}</span>
                                </div>
                                <div class="relative h-2 w-full overflow-hidden rounded-full bg-muted">
                                    <div
                                        class="absolute inset-y-0 left-0 rounded-full bg-primary"
                                        :style="{ width: `${Math.min((row.total / Math.max(totalRuns, 1)) * 100, 100)}%` }"
                                    />
                                </div>
                            </div>
                        </div>
                        <div v-else class="text-sm text-muted-foreground">
                            Пока нет запусков, чтобы построить распределение.
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div class="grid gap-4 lg:grid-cols-3">
                <Card class="lg:col-span-2">
                    <CardHeader class="pb-3">
                        <CardTitle>Лента запусков</CardTitle>
                        <CardDescription>Последние FlowRun с привязкой к потоку</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div v-if="recentRuns?.length" class="divide-y divide-border">
                            <div
                                v-for="run in recentRuns"
                                :key="run.id"
                                class="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between"
                            >
                                <div class="space-y-1">
                                    <div class="flex items-center gap-2">
                                        <Activity class="size-4 text-muted-foreground" />
                                        <span class="text-sm font-semibold">Run #{{ run.id }}</span>
                                        <Badge :class="statusTone(run.status)" variant="outline">{{ run.status ?? '—' }}</Badge>
                                    </div>
                                    <div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                                        <Link
                                            :href="flowShow({ flow: run.flow.id }).url"
                                            class="inline-flex items-center gap-1 font-semibold hover:text-primary"
                                        >
                                            {{ run.flow.name }}
                                            <ArrowUpRight class="size-3" />
                                        </Link>
                                        <Separator orientation="vertical" class="h-4" />
                                        <span>Старт: {{ formatDate(run.started_at) }}</span>
                                        <span class="text-muted-foreground">→</span>
                                        <span>Финиш: {{ formatDate(run.finished_at) }}</span>
                                    </div>
                                </div>
                                <div class="text-xs text-muted-foreground">
                                    Создано {{ formatDate(run.created_at) }}
                                </div>
                            </div>
                        </div>
                        <div v-else class="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
                            Запусков пока не было. Стартуйте потоки, чтобы собрать историю.
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Краткие метрики</CardTitle>
                        <CardDescription>Контроль точек без таблиц</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-4 text-sm text-muted-foreground">
                        <div class="flex items-center justify-between">
                            <span>В работе</span>
                            <span class="font-semibold text-foreground">{{ flowStats?.running ?? 0 }}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span>Черновики</span>
                            <span class="font-semibold text-foreground">{{ (flowStats?.total ?? 0) - (flowStats?.running ?? 0) - (flowStats?.stopped ?? 0) }}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span>Контейнеры подняты</span>
                            <span class="font-semibold text-foreground">{{ flowStats?.withContainer ?? 0 }}</span>
                        </div>
                        <div class="rounded-lg border border-dashed border-border/80 bg-muted/40 p-3">
                            <p class="text-xs text-muted-foreground">Видите странные числа? Зайдите в конкретный поток и проверьте логи запуска.</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    </AppLayout>
</template>
