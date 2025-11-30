<script setup lang="ts">
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import AppLayout from '@/layouts/AppLayout.vue';
import { create as flowCreate, index as flowsIndex, show as flowShow } from '@/routes/flows';
import type { FlowSidebarItem } from '@/types';
import { Head, Link } from '@inertiajs/vue3';
import { computed } from 'vue';
import { Activity, Clock3, FileCode, Plus, Sparkles, Workflow } from 'lucide-vue-next';

interface Flow extends FlowSidebarItem {
    description?: string | null;
    runs_count?: number;
    container_id?: string | null;
    updated_at?: string;
}

defineOptions({ layout: AppLayout });

const props = defineProps<{
    flows: Flow[];
}>();

const flowMetrics = computed(() => {
    const total = props.flows.length;
    const running = props.flows.filter((flow) => flow.status === 'running').length;
    const failing = props.flows.filter((flow) => flow.status === 'error').length;
    const drafts = props.flows.filter((flow) => !flow.status || flow.status === 'draft').length;
    const totalRuns = props.flows.reduce((sum, flow) => sum + (flow.runs_count ?? 0), 0);

    return { total, running, failing, drafts, totalRuns };
});

const statusTone = (status?: string | null) => {
    switch (status) {
        case 'running':
            return 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30';
        case 'error':
            return 'bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30';
        case 'stopped':
            return 'bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30';
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

const highlightedFlows = computed(() => props.flows.slice(0, 4));
</script>

<template>
    <Head title="Flows" />

    <div class="space-y-6 px-4 pb-12 pt-2">
        <div
            class="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-primary/10 via-background to-background p-6 shadow-sm"
        >
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,theme(colors.primary/10),transparent_45%)]" />
            <div class="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div class="space-y-2">
                    <p class="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Flow manager</p>
                    <h1 class="text-3xl font-semibold leading-tight">Ваши потоки</h1>
                    <p class="max-w-2xl text-sm text-muted-foreground">
                        Управляйте кодом, статусами и логами из единой панели. Создание и редактирование теперь вынесено
                        на отдельную страницу с конструктором.
                    </p>
                    <div class="flex flex-wrap gap-3 pt-2">
                        <Badge variant="outline" class="bg-primary/10 text-primary">{{ flowMetrics.total }} всего</Badge>
                        <Badge variant="outline" class="bg-emerald-500/10 text-emerald-300">{{ flowMetrics.running }} в работе</Badge>
                        <Badge variant="outline" class="bg-rose-500/10 text-rose-300">{{ flowMetrics.failing }} с ошибками</Badge>
                    </div>
                </div>
                <div class="flex flex-wrap gap-3">
                    <Button as-child>
                        <Link :href="flowCreate().url">
                            <Plus class="size-4" />
                            Создать flow
                        </Link>
                    </Button>
                    <Button variant="outline" as-child>
                        <Link href="/dashboard">
                            <Workflow class="size-4" />
                            Дашборд
                        </Link>
                    </Button>
                </div>
            </div>
        </div>

        <div class="grid gap-4 xl:grid-cols-[1.7fr_1fr]">
            <Card>
                <CardHeader>
                    <CardTitle>Конструктор потоков</CardTitle>
                    <CardDescription>Создание перенесено в отдельный экран: код, граф и метаданные в одном месте.</CardDescription>
                </CardHeader>
                <CardContent class="space-y-4">
                    <div class="grid gap-3 md:grid-cols-2">
                        <div class="rounded-xl border border-border/70 bg-muted/30 p-4 shadow-xs">
                            <div class="flex items-center gap-2 text-sm font-semibold">
                                <Sparkles class="size-4 text-primary" />
                                Быстрый старт
                            </div>
                            <p class="mt-1 text-sm text-muted-foreground">
                                Шаблон main.py, пустой граф и подсказки по статусам. Создайте черновик и запустите его позже.
                            </p>
                            <div class="mt-3 flex flex-wrap gap-2">
                                <Badge variant="outline" class="bg-background/70 text-muted-foreground">main.py</Badge>
                                <Badge variant="outline" class="bg-background/70 text-muted-foreground">Graph JSON</Badge>
                                <Badge variant="outline" class="bg-background/70 text-muted-foreground">Логи в UI</Badge>
                            </div>
                            <div class="mt-4 flex flex-wrap gap-3">
                                <Button as-child>
                                    <Link :href="flowCreate().url">
                                        <Plus class="size-4" />
                                        Новый flow
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
                        <div class="rounded-xl border border-border/70 bg-muted/20 p-4 shadow-xs">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2 text-sm font-semibold">
                                    <Activity class="size-4 text-muted-foreground" />
                                    Последние изменения
                                </div>
                                <Badge variant="outline" class="bg-background/80 text-muted-foreground">{{ highlightedFlows.length }} потоков</Badge>
                            </div>
                            <div v-if="highlightedFlows.length" class="mt-3 space-y-2">
                                <div
                                    v-for="flow in highlightedFlows"
                                    :key="flow.id"
                                    class="flex items-center justify-between rounded-lg border border-border/60 bg-background/60 p-3"
                                >
                                    <div class="flex flex-col">
                                        <span class="text-sm font-semibold">{{ flow.name }}</span>
                                        <span class="text-xs text-muted-foreground">{{ formatDate(flow.updated_at) }}</span>
                                    </div>
                                    <Badge :class="statusTone(flow.status)" variant="outline">
                                        {{ flow.status ?? 'draft' }}
                                    </Badge>
                                </div>
                            </div>
                            <div v-else class="mt-3 rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                                Пока нет потоков — создайте первый, чтобы увидеть историю изменений.
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card class="bg-muted/30">
                <CardHeader>
                    <CardTitle>Сводка по flows</CardTitle>
                    <CardDescription>Срез по статусам и активности</CardDescription>
                </CardHeader>
                <CardContent class="space-y-4">
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="rounded-lg border border-border/60 bg-background p-3 shadow-xs">
                            <p class="text-xs text-muted-foreground">Запусков всего</p>
                            <p class="text-2xl font-semibold">{{ flowMetrics.totalRuns }}</p>
                        </div>
                        <div class="rounded-lg border border-border/60 bg-background p-3 shadow-xs">
                            <p class="text-xs text-muted-foreground">Черновики</p>
                            <p class="text-2xl font-semibold">{{ flowMetrics.drafts }}</p>
                        </div>
                    </div>
                    <div class="space-y-2">
                        <p class="text-xs uppercase tracking-wide text-muted-foreground">Последние изменения</p>
                        <div
                            v-for="flow in props.flows.slice(0, 3)"
                            :key="flow.id"
                            class="flex items-center justify-between rounded-lg border border-border/60 bg-background/60 p-3"
                        >
                            <div class="flex flex-col">
                                <span class="text-sm font-semibold">{{ flow.name }}</span>
                                <span class="text-xs text-muted-foreground">{{ formatDate(flow.updated_at) }}</span>
                            </div>
                            <Badge :class="statusTone(flow.status)" variant="outline">
                                {{ flow.status ?? 'draft' }}
                            </Badge>
                        </div>
                        <div v-if="props.flows.length === 0" class="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                            Нет сохранённых потоков. Создайте первый, чтобы увидеть статистику.
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>

        <Card>
            <CardHeader class="pb-3">
                <div class="flex items-start justify-between gap-3">
                    <div>
                        <CardTitle>Список потоков</CardTitle>
                        <CardDescription>Статусы, описание и краткая активность</CardDescription>
                    </div>
                    <Badge variant="outline" class="bg-primary/10 text-primary">{{ flowMetrics.total }} потоков</Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div v-if="props.flows.length" class="divide-y divide-border">
                    <div
                        v-for="flow in props.flows"
                        :key="flow.id"
                        class="flex flex-col gap-2 py-3 md:flex-row md:items-center md:justify-between"
                    >
                        <div class="space-y-1">
                            <Link
                                :href="flowShow({ flow: flow.id }).url"
                                class="inline-flex items-center gap-2 text-base font-semibold hover:text-primary"
                            >
                                <Workflow class="size-4 text-muted-foreground" />
                                {{ flow.name }}
                            </Link>
                            <p class="text-sm text-muted-foreground">{{ flow.description || 'Описание не заполнено' }}</p>
                            <div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                                <span class="inline-flex items-center gap-1">
                                    <Activity class="size-3" /> Запусков: {{ flow.runs_count ?? 0 }}
                                </span>
                                <span class="inline-flex items-center gap-1">
                                    <Clock3 class="size-3" /> Обновлён: {{ formatDate(flow.updated_at) }}
                                </span>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 self-start md:self-center">
                            <Badge :class="statusTone(flow.status)" variant="outline">
                                {{ flow.status ?? 'draft' }}
                            </Badge>
                            <Button as-child variant="outline" size="sm">
                                <Link :href="flowShow({ flow: flow.id }).url">
                                    <FileCode class="size-4" />
                                    Открыть
                                </Link>
                            </Button>
                        </div>
                    </div>
                </div>
                <div v-else class="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
                    Пока нет потоков. Создайте первый, добавьте код и запустите его.
                </div>
            </CardContent>
        </Card>
    </div>
</template>
