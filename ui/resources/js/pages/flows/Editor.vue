<script setup lang="ts">
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import AppLayout from '@/layouts/AppLayout.vue';
import { index as flowsIndex } from '@/routes/flows';
import type { FlowRunSummary, FlowSidebarItem } from '@/types';
import { Head, Link, router, useForm } from '@inertiajs/vue3';
import { computed, ref, watch } from 'vue';
import { Activity, AlarmClock, ArrowLeft, Gauge, Play, Save, Square, Trash2, Workflow } from 'lucide-vue-next';

interface FlowLog {
    id: number;
    level?: string | null;
    message?: string | null;
    node_key?: string | null;
    created_at: string;
}

interface FlowDetail extends Omit<FlowSidebarItem, 'id' | 'slug'> {
    id?: number | null;
    slug?: string | null;
    description?: string | null;
    code?: string | null;
    graph?: Record<string, unknown>;
    runs_count?: number;
    container_id?: string | null;
    slug?: string | null;
    entrypoint?: string | null;
    image?: string | null;
    last_started_at?: string | null;
    last_finished_at?: string | null;
    user?: {
        name?: string | null;
    };
}

interface Permissions {
    canRun: boolean;
    canUpdate: boolean;
    canDelete: boolean;
}

interface RunStat {
    status: string;
    total: number;
}

defineOptions({ layout: AppLayout });

const props = defineProps<{
    mode: 'create' | 'edit';
    flow: FlowDetail;
    runs: FlowRunSummary[];
    logs: FlowLog[];
    status?: Record<string, any> | null;
    runStats: RunStat[];
    permissions: Permissions;
}>();

const isNew = computed(() => props.mode === 'create' || !props.flow.id);
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
            // ignore parse errors in preview
        }
    },
    { flush: 'post' },
);

const statusTone = (status?: string | null) => {
    switch (status) {
        case 'running':
            return 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30';
        case 'error':
        case 'failed':
            return 'bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30';
        case 'stopped':
        case 'success':
            return 'bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30';
        default:
            return 'bg-muted text-muted-foreground ring-1 ring-border';
    }
};

const statusLabel = computed(() => {
    if (isNew.value) {
        return 'Черновик ещё не создан';
    }

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

const saveLabel = computed(() => (isNew.value ? 'Создать flow' : 'Сохранить изменения'));
const canSave = computed(() => props.permissions.canUpdate || isNew.value);

const save = () => {
    if (!canSave.value) return;
    saving.value = true;

    const action = isNew.value
        ? form.post('/flows', {
              preserveScroll: true,
              onFinish: () => {
                  saving.value = false;
              },
          })
        : form.put(`/flows/${props.flow.id}`, {
              preserveScroll: true,
              onFinish: () => {
                  saving.value = false;
              },
          });

    return action;
};

const runFlow = () => {
    if (isNew.value || !props.permissions.canRun) return;
    router.post(`/flows/${props.flow.id}/run`);
};

const stopFlow = () => {
    if (isNew.value || !props.permissions.canRun) return;
    router.post(`/flows/${props.flow.id}/stop`);
};

const deleteFlow = () => {
    if (isNew.value || !props.permissions.canDelete) return;
    if (confirm('Удалить поток?')) {
        router.delete(`/flows/${props.flow.id}`);
    }
};

const formatDate = (value?: string | null) => {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
};

const lastRun = computed(() => props.runs?.[0]);
</script>

<template>
    <Head :title="isNew ? 'Новый flow' : form.name" />

    <div class="space-y-6 px-4 pb-12 pt-2">
        <div
            class="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-primary/10 via-background to-background p-6 shadow-sm"
        >
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,theme(colors.primary/12),transparent_45%)]" />
            <div class="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div class="space-y-3">
                    <div class="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                        <Badge variant="outline" class="bg-background/70 text-muted-foreground">
                            <Workflow class="mr-1 size-3" /> {{ isNew ? 'Новый поток' : `Flow #${props.flow.id}` }}
                        </Badge>
                        <span v-if="props.flow.slug" class="rounded-full bg-background/70 px-3 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                            {{ props.flow.slug }}
                        </span>
                    </div>
                    <h1 class="text-3xl font-semibold leading-tight">
                        {{ form.name || 'Без названия' }}
                    </h1>
                    <p class="max-w-2xl text-sm text-muted-foreground">
                        {{ form.description || 'Добавьте описание, чтобы команда понимала, что делает этот поток.' }}
                    </p>
                    <div class="flex flex-wrap gap-3 pt-1">
                        <Badge :class="statusTone(props.flow.status)" variant="outline">
                            {{ props.flow.status ?? 'draft' }}
                        </Badge>
                        <Badge variant="outline" class="bg-muted/60 text-muted-foreground">
                            Автор: {{ props.flow.user?.name ?? '—' }}
                        </Badge>
                        <Badge variant="outline" class="bg-muted/60 text-muted-foreground">
                            {{ statusLabel }}
                        </Badge>
                    </div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <Button variant="ghost" as-child>
                        <Link :href="flowsIndex().url">
                            <ArrowLeft class="size-4" />
                            К списку
                        </Link>
                    </Button>
                    <Button variant="outline" :disabled="isNew || !permissions.canRun" @click="stopFlow">
                        <Square class="size-4" />
                        Остановить
                    </Button>
                    <Button variant="outline" class="text-destructive" :disabled="isNew || !permissions.canDelete" @click="deleteFlow">
                        <Trash2 class="size-4" />
                        Удалить
                    </Button>
                    <Button variant="outline" :disabled="!canSave || form.processing" @click="save">
                        <Save class="size-4" />
                        {{ saveLabel }}
                    </Button>
                    <Button :disabled="isNew || !permissions.canRun" @click="runFlow">
                        <Play class="size-4" />
                        Запустить
                    </Button>
                </div>
            </div>

            <div class="relative mt-6 grid gap-3 lg:grid-cols-4">
                <Card class="border border-border/80 bg-background/70 shadow-xs">
                    <CardHeader class="pb-2">
                        <CardDescription>Запусков всего</CardDescription>
                        <CardTitle class="text-2xl">{{ props.flow.runs_count ?? props.runs?.length ?? 0 }}</CardTitle>
                    </CardHeader>
                    <CardContent class="text-sm text-muted-foreground">
                        Последний: {{ formatDate(lastRun?.started_at) }}
                    </CardContent>
                </Card>
                <Card class="border border-border/80 bg-background/70 shadow-xs">
                    <CardHeader class="pb-2">
                        <CardDescription>Последний старт</CardDescription>
                        <CardTitle class="text-2xl">{{ formatDate(props.flow.last_started_at) }}</CardTitle>
                    </CardHeader>
                    <CardContent class="text-sm text-muted-foreground">
                        Финиш: {{ formatDate(props.flow.last_finished_at) }}
                    </CardContent>
                </Card>
                <Card class="border border-border/80 bg-background/70 shadow-xs">
                    <CardHeader class="pb-2">
                        <CardDescription>Распределение статусов</CardDescription>
                    </CardHeader>
                    <CardContent class="flex flex-wrap gap-2 pt-2">
                        <Badge
                            v-for="stat in props.runStats"
                            :key="stat.status"
                            variant="outline"
                            class="bg-muted/50 text-muted-foreground"
                        >
                            {{ stat.status }} • {{ stat.total }}
                        </Badge>
                        <span v-if="!props.runStats.length" class="text-sm text-muted-foreground">Пока нет запусков</span>
                    </CardContent>
                </Card>
                <Card class="border border-border/80 bg-background/70 shadow-xs">
                    <CardHeader class="pb-2">
                        <CardDescription>Контейнер</CardDescription>
                        <CardTitle class="text-2xl truncate">
                            {{ props.flow.container_id ?? 'Ещё не создан' }}
                        </CardTitle>
                    </CardHeader>
                    <CardContent class="text-sm text-muted-foreground">
                        {{ props.flow.image ?? 'flow:dev' }} • {{ props.flow.entrypoint ?? 'main.py' }}
                    </CardContent>
                </Card>
            </div>
        </div>

        <div class="grid gap-4 xl:grid-cols-[2fr,1fr]">
            <div class="space-y-4">
                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Описание</CardTitle>
                        <CardDescription>Название, назначение и заметки</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-4">
                        <div class="space-y-2">
                            <Label for="flow-name">Название</Label>
                            <Input id="flow-name" v-model="form.name" required placeholder="Например, ETL nightly" />
                            <p v-if="form.errors.name" class="text-sm text-destructive">{{ form.errors.name }}</p>
                        </div>
                        <div class="space-y-2">
                            <Label for="flow-description">Описание</Label>
                            <Textarea
                                id="flow-description"
                                v-model="form.description"
                                placeholder="Что делает поток? Какие сервисы затрагивает?"
                                class="min-h-[90px]"
                            />
                        </div>
                        <div class="flex flex-wrap gap-3">
                            <Button type="button" :disabled="form.processing || !canSave" @click="save">
                                <Save class="size-4" />
                                {{ saveLabel }}
                            </Button>
                            <p class="text-xs text-muted-foreground">Сохраните изменения перед запуском.</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Код</CardTitle>
                        <CardDescription>main.py, который отправится в рантайм</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3">
                        <div class="flex items-center gap-3 text-sm text-muted-foreground">
                            <Badge variant="outline" class="bg-muted/60 text-muted-foreground">main.py</Badge>
                            <span class="inline-flex items-center gap-2">
                                <Gauge class="size-4" /> Статус: {{ props.flow.status ?? 'draft' }}
                            </span>
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
                        <CardTitle>Граф (JSON)</CardTitle>
                        <CardDescription>nodes/edges для визуализации и оркестрации</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3">
                        <div class="flex items-center justify-between text-xs text-muted-foreground">
                            <span>Пример: { nodes: [], edges: [] }</span>
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
                        <CardTitle>Мониторинг</CardTitle>
                        <CardDescription>Быстрый взгляд на доступность и исполнение</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-3 text-sm text-muted-foreground">
                        <div class="flex items-center justify-between">
                            <span class="inline-flex items-center gap-2 text-foreground">
                                <Activity class="size-4 text-muted-foreground" /> Запусков
                            </span>
                            <span class="font-semibold text-foreground">{{ props.flow.runs_count ?? props.runs?.length ?? 0 }}</span>
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
                        <Separator />
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
                        <div v-if="props.runs?.length" class="max-h-80 space-y-3 overflow-y-auto pr-1">
                            <div
                                v-for="run in props.runs"
                                :key="run.id"
                                class="rounded-lg border border-border/60 bg-muted/30 p-3"
                            >
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-semibold">Запуск #{{ run.id }}</span>
                                    <Badge :class="statusTone(run.status)" variant="outline">{{ run.status ?? '—' }}</Badge>
                                </div>
                                <p class="text-xs text-muted-foreground">
                                    {{ formatDate(run.started_at) }} → {{ formatDate(run.finished_at) }}
                                </p>
                            </div>
                        </div>
                        <div v-else class="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                            Запусков еще не было. Сохраните и запустите поток.
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader class="pb-3">
                        <CardTitle>Логи</CardTitle>
                        <CardDescription>Последние сообщения рантайма</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div v-if="props.logs?.length" class="max-h-96 space-y-2 overflow-y-auto pr-1">
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
                            Логи появятся после первого запуска.
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    </div>
</template>
