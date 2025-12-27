<script setup lang="ts">
import { Head } from '@inertiajs/vue3';

import AppearanceTabs from '@/components/AppearanceTabs.vue';
import HeadingSmall from '@/components/HeadingSmall.vue';
import LanguageTabs from '@/components/LanguageTabs.vue';
import { type BreadcrumbItem } from '@/types';

import AppLayout from '@/layouts/AppLayout.vue';
import SettingsLayout from '@/layouts/settings/Layout.vue';
import { edit } from '@/routes/appearance';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const breadcrumbItems = computed<BreadcrumbItem[]>(() => [
    {
        title: t('settings.appearance.title'),
        href: edit().url,
    },
]);
</script>

<template>
    <AppLayout :breadcrumbs="breadcrumbItems">
        <Head :title="t('settings.appearance.title')" />

        <SettingsLayout>
            <div class="space-y-10">
                <div class="space-y-6">
                    <HeadingSmall
                        :title="t('settings.appearance.title')"
                        :description="t('settings.appearance.description')"
                    />
                    <AppearanceTabs />
                </div>

                <div class="space-y-6">
                    <HeadingSmall
                        :title="t('settings.language.title')"
                        :description="t('settings.language.description')"
                    />
                    <LanguageTabs />
                </div>
            </div>
        </SettingsLayout>
    </AppLayout>
</template>
