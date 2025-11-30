<script setup>
    import AppLayout from "@/Layouts/AppLayout.vue";
    import {Link, useForm} from "@inertiajs/vue3";

    defineOptions({layout: AppLayout});

    const props = defineProps({
        flows: {
            type: Array,
            default: () => [],
        },
    });

    const createForm = useForm({
        name: "",
        description: "",
        code: `from kawa import ActorSystem\n\n# entry point\nif __name__ == "__main__":\n    print("hello from kawaflow")\n`,
        graph: {
            nodes: [],
            edges: [],
        },
    });

    const createFlow = () => {
        createForm.post("/flows", {
            preserveScroll: true,
            onSuccess: () => createForm.reset("name", "description"),
        });
    };

    const statusColor = (status) => {
        if (status === "running") return "bg-emerald-500/20 text-emerald-300";
        if (status === "error") return "bg-rose-500/20 text-rose-300";
        if (status === "stopped") return "bg-amber-500/20 text-amber-300";
        return "bg-slate-700 text-slate-200";
    };
</script>

<template>
    <div class="space-y-6">
        <div
            class="flex flex-col gap-3 border-b border-slate-800 pb-4 md:flex-row md:items-center md:justify-between">
            <div>
                <p class="text-sm uppercase tracking-widest text-slate-500">Flows</p>
                <h1 class="text-2xl font-semibold text-slate-100">Ваши потоки</h1>
                <p class="text-sm text-slate-400">Админ видит все, обычный пользователь — только свои.</p>
            </div>
            <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-sm text-slate-200">
                Всего: <span class="font-semibold text-sky-300">{{ props.flows.length }}</span>
            </div>
        </div>

        <div class="grid gap-4 lg:grid-cols-[2fr_3fr]">
            <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <h2 class="text-lg font-semibold text-slate-100">Новый flow</h2>
                <form class="mt-4 space-y-4" @submit.prevent="createFlow">
                    <div>
                        <label class="mb-1 block text-sm text-slate-300">Название</label>
                        <input
                            v-model="createForm.name"
                            type="text"
                            required
                            class="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                        />
                        <p v-if="createForm.errors.name" class="mt-1 text-sm text-rose-400">
                            {{ createForm.errors.name }}</p>
                    </div>
                    <div>
                        <label class="mb-1 block text-sm text-slate-300">Описание</label>
                        <textarea
                            v-model="createForm.description"
                            rows="2"
                            class="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                            placeholder="Что делает поток?"
                        />
                    </div>
                    <div>
                        <label class="mb-1 block text-sm text-slate-300">Стартовый код</label>
                        <textarea
                            v-model="createForm.code"
                            rows="6"
                            class="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-sm text-slate-100 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/40"
                        />
                    </div>
                    <button
                        type="submit"
                        class="w-full rounded-lg bg-sky-500 px-4 py-2 font-semibold text-slate-900 transition hover:bg-sky-400 disabled:opacity-50"
                        :disabled="createForm.processing"
                    >
                        Создать flow
                    </button>
                </form>
            </div>

            <div class="space-y-4">
                <div
                    v-for="flow in props.flows"
                    :key="flow.id"
                    class="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow"
                >
                    <div class="flex items-center justify-between gap-3">
                        <div>
                            <Link :href="`/flows/${flow.id}`"
                                  class="text-lg font-semibold text-slate-100 hover:text-sky-300">
                                {{ flow.name }}
                            </Link>
                            <p class="text-sm text-slate-400">{{ flow.description }}</p>
                        </div>
                        <span class="rounded-full px-3 py-1 text-xs font-semibold"
                              :class="statusColor(flow.status)">
              {{ flow.status || "draft" }}
            </span>
                    </div>
                    <div class="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">
                        <span class="rounded bg-slate-800 px-2 py-1">Запусков: {{ flow.runs_count }}</span>
                        <span v-if="flow.container_id" class="rounded bg-slate-800 px-2 py-1">Container: {{
                                flow.container_id.slice(0, 8)
                            }}</span>
                    </div>
                </div>
                <div v-if="!props.flows.length"
                     class="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-slate-400">
                    Пока нет потоков. Создайте первый, добавьте код и граф, затем запустите.
                </div>
            </div>
        </div>
    </div>
</template>
