-- 在 Supabase Dashboard → SQL Editor 貼上執行
create table if not exists public.workout_logs (
    id         bigint generated always as identity primary key,
    exercise   text          not null,
    weight_kg  numeric(6,2)  not null check (weight_kg >= 0),
    reps       integer       not null check (reps > 0),
    created_at timestamptz   not null default now()
);

create index if not exists workout_logs_created_at_idx
    on public.workout_logs (created_at);

-- 開啟 RLS：沒有任何 policy 時，anon key 無法讀寫。
-- 做法 A（建議）：secrets.toml 放 service_role key（只在 Streamlit 伺服器端使用，不要 commit 進 git）。
-- 做法 B：改用 anon key，並取消下面兩段註解建立 policy（任何拿到 anon key 的人都能讀寫）。
alter table public.workout_logs enable row level security;

-- create policy "anon can insert" on public.workout_logs for insert to anon with check (true);
-- create policy "anon can read"   on public.workout_logs for select to anon using (true);
