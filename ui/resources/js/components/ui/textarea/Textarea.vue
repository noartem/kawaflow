<script setup lang="ts">
import { cn } from '@/lib/utils';
import { useVModel } from '@vueuse/core';
import type { HTMLAttributes } from 'vue';

const props = defineProps<{
    defaultValue?: string | number | null;
    modelValue?: string | number | null;
    class?: HTMLAttributes['class'];
}>();

const emits = defineEmits<{
    (e: 'update:modelValue', payload: string | number | null): void;
}>();

const modelValue = useVModel(props, 'modelValue', emits, {
    passive: true,
    defaultValue: props.defaultValue ?? '',
});
</script>

<template>
    <textarea
        v-model="modelValue"
        data-slot="textarea"
        :class="
            cn(
                'flex min-h-[120px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-sm ring-offset-background transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                props.class,
            )
        "
        v-bind="$attrs"
    />
</template>
