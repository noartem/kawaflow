<script setup lang="ts">
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import AppLayout from '@/layouts/AppLayout.vue';
import { Head, router, useForm } from '@inertiajs/vue3';
import { computed, ref, watch } from 'vue';
import { Activity, AlarmClock, Play, Save, Square, Trash2 } from 'lucide-vue-next';
import type { FlowRunSummary, FlowSidebarItem } from '@/types';

interface FlowLog {
    id: number;
    level?: string | null;
    message?: string | null;
    node_key?: string | null;
    created_at: string;
}

interface FlowDetail extends FlowSidebarItem {
    description?: string | null;
    code?: string | null;
    graph?: Record<string, unknown>;
    runs_count?: number;
    container_id?: string | null;
    slug?: string;
    last_started_at?: string | null;
    last_finished_at?: string | null;
    user?: {
        name?: string | null;
    };
}

defineOptions({ layout: AppLayout });

const props = defineProps<{
    flow: FlowDetail;
    runs: FlowRunSummary[];
    logs: FlowLog[];
    status?: Record<string, any> | null;
}>();

const saving = ref(false);
const form = useForm({
    name: props.flow.name,
    description: props.flow.description || '',
    code: props.flow.code || '',
    graph: props.flow.graph || { nodes: [], edges: [] },
});
const graphText = ref(JSON.stringify(form.graph, null, 2));

watch(
    graphText,
    (value) => {
        try {
            form.graph = JSON.parse(value || '{}');
        } catch (error) {
            // ignore parse errors
        }
    },
    { flush: 'post' },
);

const formatDate = (value?: string | null) => {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
};

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

const statusLabel = computed(() => {
    const info = props.status?.data || props.status;
    if (!info) return 'Нет статуса';
    if ((info as any).error) return (info as any).message || 'Ошибка статуса';
    if ((info as any).state) {
        return `${(info as any).state} / ${(info as any).health ?? 'n/a'}`;
    }
    if ((info as any).event === 'container_status') {
        return `${(info as any).data?.state ?? 'unknown'} / ${(info as any).data?.health ?? 'unknown'}`;
    }
    return 'Статус получен';
});

const save = () => {
    saving.value = true;
    form.put(`/flows/${props.flow.id}`, {
        onFinish: () => {
            saving.value = false;
        },
    });
};

const runFlow = () => router.post(`/flows/${props.flow.id}/run`);
const stopFlow = () => router.post(`/flows/${props.flow.id}/stop`);
const deleteFlow = () => {
    if (confirm('Удалить поток?')) {
        router.delete(`/flows/${props.flow.id}`);
    }
};
</script>

<template>
    <Head :title="props.flow.name" />

    <div class="space-y-6 px-4 pb-12 pt-2">
        <div
            class="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-primary/10 via-background to-background p-6 shadow-sm"
        >
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_top,theme(colors.primary/10),transparent_35%)]" />
            <div class="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div class="space-y-2">
                    <p class="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Flow details</p>
                    <h1 class="text-3xl font-semibold leading-tight">{{ form.name }}</h1>
                    <p class="text-sm text-muted-foreground">
                        {{ props.flow.slug }} • {{ statusLabel }}
                    </p>
                    <div class="flex flex-wrap gap-3 pt-2">
                        <Badge :class="statusTone(props.flow.status)" variant="outline">
                            {{ props.flow.status ?? 'draft' }}
                        </Badge>
                        <Badge variant="outline" class="bg-muted/60 text-muted-foreground">
                            Автор: {{ props.flow.user?.name ?? '—' }}
                        </Badge>
                    </div>
                </div>
                <div class="flex flex-wrap gap-3">
                    <Button variant="outline" @click="stopFlow">
                        <Square class="size-4" />
                        Остановить
                    </Button>
                    <Button variant="outline" class="text-destructive" @click="deleteFlow">
                        <Trash2 class="size-4" />
                        Удалить
                    </Button>
                    <Button @click="runFlow">
                        <Play class="size-4" />
                        Запустить
                    </Button>
                </div>
            </div>
        </div>

        <div class="grid gap-4 lg:grid-cols-[2fr_1.05fr]">
            <div class="space-y-4">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Python скрипт</CardTitle>
                        <CardDescription>Сохраняется в volume и отдаётся рантайму</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3">
                        <div class="flex items-center gap-3">
                            <Label for="flow-code" class="text-sm font-medium">Код</Label>
                            <Badge variant="outline" class="bg-muted/60 text-muted-foreground">main.py</Badge>
                            <Button
                                variant="outline"
                                size="sm"
                                class="ml-auto"
                                type="button"
                                :disabled="saving || form.processing"
                                @click="save"
                            >
                                <Save class="size-4" />
                                Сохранить
                            </Button>
                        </div>
                        <Textarea
                            id="flow-code"
                            v-model="form.code"
                            class="font-mono"
                            rows="18"
                        />
                        <p v-if="form.errors.code" class="text-sm text-destructive">{{ form.errors.code }}</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>JSON граф</CardTitle>
                        <CardDescription>nodes/edges для визуализации</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3">
                        <div class="flex items-center justify-between text-xs text-muted-foreground">
                            <span>ожидает { nodes: [], edges: [] }</span>
                            <Badge variant="outline" class="bg-muted/60 text-muted-foreground">{{ typeof form.graph }}</Badge>
                        </div>
                        <Textarea v-model="graphText" class="font-mono text-xs" rows="10" />
                        <p v-if="form.errors.graph" class="text-sm text-destructive">{{ form.errors.graph }}</p>
                    </CardContent>
                </Card>
            </div>

            <div class="space-y-4">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Быстрые метрики</CardTitle>
                        <CardDescription>Контрольная панель по потоку</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3 text-sm text-muted-foreground">
                        <div class="flex items-center justify-between">
                            <span class="inline-flex items-center gap-2 text-foreground">
                                <Activity class="size-4 text-muted-foreground" /> Запусков
                            </span>
                            <span class="font-semibold text-foreground">{{ props.flow.runs_count ?? 0 }}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="inline-flex items-center gap-2 text-foreground">
                                <AlarmClock class="size-4 text-muted-foreground" /> Последний старт
                            </span>
                            <span class="font-semibold text-foreground">{{ formatDate(props.flow.last_started_at) }}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="inline-flex items-center gap-2 text-foreground">
                                <Square class="size-4 text-muted-foreground" /> Последний финиш
                            </span>
                            <span class="font-semibold text-foreground">{{ formatDate(props.flow.last_finished_at) }}</span>
                        </div>
                        <div class="rounded-lg border border-dashed border-border p-3 text-xs text-muted-foreground">
                            {{ props.flow.container_id ? `Container: ${props.flow.container_id}` : 'Контейнер ещё не создан' }}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Запуски</CardTitle>
                        <CardDescription>Последние исполнения</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div v-if="props.runs?.length" class="divide-y divide-border">
                            <div v-for="run in props.runs" :key="run.id" class="space-y-1 py-3">
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-semibold">#{{ run.id }}</span>
                                    <Badge :class="statusTone(run.status)" variant="outline">{{ run.status ?? '—' }}</Badge>
                                </div>
                                <p class="text-xs text-muted-foreground">
                                    {{ formatDate(run.started_at) }} → {{ formatDate(run.finished_at) }}
                                </p>
                            </div>
                        </div>
                        <div v-else class="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                            Запусков еще не было.
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Логи</CardTitle>
                        <CardDescription>Последние сообщения</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div v-if="props.logs?.length" class="max-h-80 space-y-2 overflow-y-auto">
                            <div
                                v-for="log in props.logs"
                                :key="log.id"
                                class="rounded-lg border border-border bg-muted/40 p-3"
                            >
                                <div class="flex items-center justify-between text-xs text-muted-foreground">
                                    <span class="uppercase tracking-wide">{{ log.level }}</span>
                                    <span>{{ formatDate(log.created_at) }}</span>
                                </div>
                                <p class="mt-2 text-sm text-foreground">{{ log.message }}</p>
                                <p v-if="log.node_key" class="text-xs text-muted-foreground">Нода: {{ log.node_key }}</p>
                            </div>
                        </div>
                        <div v-else class="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                            Пока нет логов.
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    </div>
</template>
