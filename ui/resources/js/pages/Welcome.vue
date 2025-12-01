<script setup lang="ts">
import { login, register } from '@/routes';
import {Head, Link, router} from '@inertiajs/vue3';
import {Button} from "@/components/ui/button";

withDefaults(
    defineProps<{
        canRegister: boolean;
    }>(),
    {
        canRegister: true,
    },
);
</script>

<template>
    <Head title="Welcome" />

    <main class="flex flex-col min-h-screen items-center justify-center gap-4">
        <h1 class="text-6xl font-bold">
            Kawaflow
        </h1>

        <div class="flex gap-4">
            <Link :href="login()">
                <Button @click="router.visit(login)">Login</Button>
            </Link>

            <Link v-if="canRegister" :href="register()">
                <Button>Register</Button>
            </Link>
        </div>
    </main>
</template>
