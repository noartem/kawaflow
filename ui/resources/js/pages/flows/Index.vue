<script setup lang="ts">
    import {Badge} from '@/components/ui/badge';
    import {Button} from '@/components/ui/button';
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
    import AppLayout from '@/layouts/AppLayout.vue';
    import {create as flowCreate, index as flowsIndex, show as flowShow} from '@/routes/flows';
    import type {BreadcrumbItem, FlowSidebarItem} from '@/types';
    import {Head, Link} from '@inertiajs/vue3';
    import {computed} from 'vue';
    import {Activity, Clock3, FileCode, Plus, Workflow} from 'lucide-vue-next';

    interface Flow extends FlowSidebarItem {
        description?: string | null;
        runs_count?: number;
        container_id?: string | null;
        updated_at?: string;
    }

    const props = defineProps<{
        flows: Array<Flow>;
    }>();

    const breadcrumbs: BreadcrumbItem[] = [
        {
            title: 'Flows',
            href: flowsIndex().url,
        },
    ];

    const metrics = computed(() => {
        const total = props.flows.length;
        const running = props.flows.filter((flow) => flow.status === 'running').length;
        const failing = props.flows.filter((flow) => flow.status === 'error').length;
        const drafts = props.flows.filter((flow) => !flow.status || flow.status === 'draft').length;
        const totalRuns = props.flows.reduce((sum, flow) => sum + (flow.runs_count ?? 0), 0);

        return {total, running, failing, drafts, totalRuns};
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
</script>

<template>
    <Head title="Flows"/>

    <AppLayout :breadcrumbs="breadcrumbs">
        <div class="space-y-6 px-4 pb-12 pt-2">
            <div
                class="relative overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-primary/10 via-background to-background p-6 shadow-sm"
            >
                <div
                    class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,theme(colors.primary/10),transparent_45%)]"/>

                <div class="relative flex flex-col gap-8 lg:flex-row lg:items-center">
                    <div class="space-y-1">
                        <h1 class="text-3xl font-semibold leading-tight">Ваши потоки</h1>
                        <div class="flex flex-wrap gap-3 pt-2">
                            <Badge variant="outline" class="bg-primary/10 text-primary">{{ metrics.total }} всего
                            </Badge>
                            <Badge

                                v-if="metrics.running > 0"
                                variant="outline" class="bg-emerald-500/10 text-emerald-300">{{ metrics.running }} в
                                работе
                            </Badge>
                            <Badge
                                v-if="metrics.failing > 0"
                                variant="outline" class="bg-rose-500/10 text-rose-300">{{ metrics.failing }} с
                                ошибками
                            </Badge>
                            <Badge
                                v-if="metrics.drafts > 0"
                                variant="outline" class="bg-muted/60 text-muted-foreground">{{ metrics.drafts }}
                                черновиков
                            </Badge>
                        </div>
                    </div>

                    <div class="flex-1"/>

                    <div class="flex flex-wrap gap-3">
                        <Button as-child>
                            <Link :href="flowCreate().url">
                                <Plus class="size-4"/>
                                Создать flow
                            </Link>
                        </Button>
                    </div>
                </div>
            </div>

            <Card>
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
                                    <Workflow class="size-4 text-muted-foreground"/>
                                    {{ flow.name }}
                                </Link>
                                <p class="text-sm text-muted-foreground">{{
                                        flow.description || 'Описание не заполнено'
                                    }}</p>
                                <div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                                    <span class="inline-flex items-center gap-1">
                                        <Activity class="size-3"/> Запусков: {{ flow.runs_count ?? 0 }}
                                    </span>
                                    <span class="inline-flex items-center gap-1">
                                        <Clock3 class="size-3"/> Обновлён: {{ formatDate(flow.updated_at) }}
                                    </span>
                                </div>
                            </div>
                            <div class="flex items-center gap-3 self-start md:self-center">
                                <Badge :class="statusTone(flow.status)" variant="outline">
                                    {{ flow.status ?? 'draft' }}
                                </Badge>
                                <Button as-child variant="outline" size="sm">
                                    <Link :href="flowShow({ flow: flow.id }).url">
                                        <FileCode class="size-4"/>
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
    </AppLayout>
</template>
