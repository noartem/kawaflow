<script setup>
    // import FlowGraph from "@/Components/FlowGraph.vue";
    import AppLayout from "@/layouts/AppLayout.vue";
    import {router, useForm} from "@inertiajs/vue3";
    import {computed, ref} from "vue";

    defineOptions({layout: AppLayout});

    const props = defineProps({
        flow: Object,
        runs: Array,
        logs: Array,
        status: Object,
    });

    const saving = ref(false);
    const form = useForm({
        name: props.flow.name,
        description: props.flow.description || "",
        code: props.flow.code || "",
        graph: props.flow.graph || {nodes: [], edges: []},
    });
    const graphText = ref(JSON.stringify(form.graph, null, 2));

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
        if (confirm("Удалить поток?")) {
            router.delete(`/flows/${props.flow.id}`);
        }
    };

    const syncGraph = (event) => {
        try {
            const parsed = JSON.parse(event.target.value || "{}");
            form.graph = parsed;
            graphText.value = JSON.stringify(parsed, null, 2);
        } catch (error) {
            // ignore parse errors, user will see stale graph
        }
    };

    const statusBadge = computed(() => {
        const value = props.flow.status || "draft";
        const map = {
            running: "bg-emerald-500/20 text-emerald-200",
            stopped: "bg-amber-500/20 text-amber-200",
            error: "bg-rose-500/20 text-rose-200",
            draft: "bg-slate-700 text-slate-200",
            starting: "bg-sky-500/20 text-sky-200",
        };
        return map[value] || map.draft;
    });

    const statusLabel = computed(() => {
        const info = props.status?.data || props.status;
        if (!info) return "Нет статуса";
        if (info.error) return info.message || "Ошибка статуса";
        if (info.state) {
            return `${info.state} / ${info.health ?? "n/a"}`;
        }
        if (info.event === "container_status") {
            return `${info.data?.state ?? "unknown"} / ${info.data?.health ?? "unknown"}`;
        }
        return "Статус получен";
    });
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <div
                class="flex flex-col gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <p class="text-sm uppercase tracking-widest text-slate-500">Flow</p>
                    <h1 class="text-2xl font-semibold text-slate-100">{{ form.name }}</h1>
                    <p class="text-sm text-slate-400">
                        {{ props.flow.slug }} • {{ statusLabel }}
                    </p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
        <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadge">
          {{ props.flow.status || "draft" }}
        </span>
                    <button
                        class="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400"
                        type="button"
                        @click="runFlow"
                    >
                        Запустить
                    </button>
                    <button
                        class="rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-amber-400"
                        type="button"
                        @click="stopFlow"
                    >
                        Остановить
                    </button>
                    <button
                        class="rounded-lg bg-rose-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-rose-400"
                        type="button"
                        @click="deleteFlow"
                    >
                        Удалить
                    </button>
                </div>
            </div>

            <div class="grid gap-4 lg:grid-cols-[2fr_1fr]">
                <div class="space-y-4">
                    <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <h2 class="text-lg font-semibold text-slate-100">Python скрипт</h2>
                                <p class="text-sm text-slate-400">Сохраняется в volume и отдается рантайму</p>
                            </div>
                            <button
                                class="rounded-lg bg-sky-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-sky-400 disabled:opacity-50"
                                type="button"
                                :disabled="saving || form.processing"
                                @click="save"
                            >
                                Сохранить
                            </button>
                        </div>
                        <textarea
                            v-model="form.code"
                            rows="18"
                            class="mt-4 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-sm text-slate-100 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                        />
                        <p v-if="form.errors.code" class="mt-2 text-sm text-rose-400">{{ form.errors.code }}</p>
                    </div>

                    <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <h2 class="text-lg font-semibold text-slate-100">JSON граф</h2>
                                <p class="text-sm text-slate-400">nodes/edges для визуализации</p>
                            </div>
                            <span class="text-xs text-slate-400">ожидает { nodes: [], edges: [] }</span>
                        </div>
                        <textarea
                            v-model="graphText"
                            @input="syncGraph"
                            rows="10"
                            class="mt-3 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-100 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                        />
                        <p v-if="form.errors.graph" class="mt-2 text-sm text-rose-400">{{ form.errors.graph }}</p>
                        <div class="mt-3">
                            {{ form.graph }}
<!--                            <FlowGraph :graph="form.graph"/>-->
                        </div>
                    </div>
                </div>

                <div class="space-y-4">
                    <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <h3 class="text-lg font-semibold text-slate-100">Статус контейнера</h3>
                        <div class="mt-3 space-y-2 text-sm text-slate-300">
                            <p v-if="!props.flow.container_id" class="text-slate-500">Контейнер ещё не создан</p>
                            <template v-else>
                                <p><span class="text-slate-500">ID:</span> {{ props.flow.container_id }}</p>
                                <p><span class="text-slate-500">Состояние:</span> {{ statusLabel }}</p>
                                <p v-if="props.status?.data?.uptime">
                                    <span class="text-slate-500">Uptime:</span> {{ props.status.data.uptime }}
                                </p>
                            </template>
                        </div>
                    </div>

                    <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <h3 class="text-lg font-semibold text-slate-100">Запуски</h3>
                        <div v-if="runs?.length" class="mt-3 space-y-2 text-sm">
                            <div
                                v-for="run in runs"
                                :key="run.id"
                                class="rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                            >
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-200">#{{ run.id }}</span>
                                    <span class="text-xs text-slate-400">{{ run.status }}</span>
                                </div>
                                <p class="text-xs text-slate-500">
                                    {{ run.started_at || "—" }} → {{ run.finished_at || "..." }}
                                </p>
                            </div>
                        </div>
                        <div v-else class="mt-3 text-sm text-slate-500">Запусков еще не было.</div>
                    </div>

                    <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <h3 class="text-lg font-semibold text-slate-100">Логи</h3>
                        <div v-if="logs?.length" class="mt-3 max-h-72 space-y-2 overflow-y-auto text-sm">
                            <div
                                v-for="log in logs"
                                :key="log.id"
                                class="rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                            >
                                <div class="flex items-center justify-between text-xs text-slate-400">
                                    <span class="uppercase tracking-wide">{{ log.level }}</span>
                                    <span>{{ log.created_at }}</span>
                                </div>
                                <p class="mt-2 text-slate-100">{{ log.message }}</p>
                                <p v-if="log.node_key" class="text-xs text-slate-400">Нода: {{ log.node_key }}</p>
                            </div>
                        </div>
                        <div v-else class="mt-3 text-sm text-slate-500">Пока нет логов.</div>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
