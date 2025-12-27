<script setup lang="ts">
import { login, register } from '@/routes';
import { Head, Link, router } from '@inertiajs/vue3';
import { Button } from '@/components/ui/button';
import { useI18n } from 'vue-i18n';

withDefaults(
    defineProps<{
        canRegister: boolean;
    }>(),
    {
        canRegister: true,
    },
);

const { t } = useI18n();
</script>

<template>
    <Head :title="t('nav.welcome')" />

    <main class="flex flex-col min-h-screen items-center justify-center gap-4">
        <h1 class="text-6xl font-bold">
            {{ t('app.name') }}
        </h1>

        <div class="flex gap-4">
            <Link :href="login()">
                <Button @click="router.visit(login)">{{ t('auth.login.short') }}</Button>
            </Link>

            <Link v-if="canRegister" :href="register()">
                <Button>{{ t('auth.register.short') }}</Button>
            </Link>
        </div>
    </main>
</template>
