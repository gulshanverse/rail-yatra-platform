'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowRight,
  Bot,
  CalendarDays,
  Check,
  ChevronRight,
  CircleUserRound,
  Clock3,
  Compass,
  Gauge,
  Home,
  MapPin,
  Menu,
  Moon,
  Search,
  ShieldCheck,
  Sparkles,
  Ticket,
  TrainFront,
  UserRound,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/cn';

export const HERO_SCENES = [
  {
    eyebrow: 'The journey is part of the destination',
    title: 'Go farther. Travel wiser.',
    description: 'RailYatra combines railway intelligence, live context, and Yatri AI to make every Indian rail journey feel considered.',
    image: 'https://images.unsplash.com/photo-1534423861386-85a1ca0b3f6d?auto=format&fit=crop&w=2200&q=85',
    tone: 'from-[#071521]/95 via-[#071521]/55 to-transparent',
  },
  {
    eyebrow: 'A quieter way to travel',
    title: 'See India from the window seat.',
    description: 'Compare routes by the things that matter: certainty, comfort, arrival time, and the rhythm of your trip.',
    image: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=2200&q=85',
    tone: 'from-[#0e1a2c]/95 via-[#0e1a2c]/55 to-transparent',
  },
  {
    eyebrow: 'Intelligence for the in-between',
    title: 'From first search to final station.',
    description: 'Plan with confidence, keep your ticket close, and know what is next before the platform announcement.',
    image: 'https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=2200&q=85',
    tone: 'from-[#17120b]/95 via-[#17120b]/55 to-transparent',
  },
];

const NAV_ITEMS = [
  { href: '/', label: 'Explore', icon: Compass },
  { href: '/plan', label: 'Plan', icon: MapPin },
  { href: '/search', label: 'Trains', icon: TrainFront },
  { href: '/trips', label: 'Trips', icon: Ticket },
  { href: '/live', label: 'Live', icon: Gauge },
  { href: '/chat', label: 'Yatri', icon: Bot },
];

function isActive(pathname: string, href: string) {
  return href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(`${href}/`);
}

export function TravelHeader() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <header className="relative z-40 border-b border-white/10 bg-[#07111f]/90 text-white backdrop-blur-xl">
        <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between px-5 sm:px-8 lg:px-12">
          <Link href="/" className="group flex items-center gap-3" aria-label="RailYatra home">
            <span className="grid h-10 w-10 place-items-center rounded-[13px] bg-[#e7b75e] text-[#07111f] shadow-[0_8px_30px_rgba(231,183,94,.25)] transition-transform duration-200 group-hover:-rotate-3">
              <TrainFront className="h-5 w-5" strokeWidth={2.4} />
            </span>
            <span>
              <span className="block font-serif text-xl font-semibold tracking-[-0.03em]">RailYatra</span>
              <span className="hidden text-[10px] font-medium uppercase tracking-[0.22em] text-[#a9b8c9] sm:block">Travel intelligence</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
            {NAV_ITEMS.map(({ href, label }) => {
              const active = isActive(pathname, href);
              return (
                <Link key={href} href={href} aria-current={active ? 'page' : undefined} className={cn('relative rounded-full px-4 py-2 text-sm transition-colors duration-200', active ? 'bg-white/10 text-white' : 'text-[#9fafc0] hover:bg-white/5 hover:text-white')}>
                  {label}
                  {active && <span className="absolute inset-x-4 -bottom-[17px] h-px bg-[#e7b75e]" />}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-2">
            <Link href="/chat" className="hidden min-h-11 items-center gap-2 rounded-full border border-[#e7b75e]/40 px-4 text-sm font-medium text-[#f4d58d] transition hover:bg-[#e7b75e]/10 sm:flex">
              <Sparkles className="h-4 w-4" />
              Plan with Yatri
            </Link>
            <Link href="/settings" className="grid h-11 w-11 place-items-center rounded-full border border-white/10 text-[#a9b8c9] transition hover:bg-white/10 hover:text-white" aria-label="Open profile">
              <CircleUserRound className="h-[19px] w-[19px]" />
            </Link>
            <button type="button" className="grid h-11 w-11 place-items-center rounded-full border border-white/10 text-[#a9b8c9] lg:hidden" onClick={() => setMobileOpen((value) => !value)} aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={mobileOpen}>
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
        <AnimatePresence>
          {mobileOpen && (
            <motion.nav initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="border-t border-white/10 bg-[#07111f] px-5 py-3 lg:hidden" aria-label="Mobile navigation">
              {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href} onClick={() => setMobileOpen(false)} className={cn('flex min-h-12 items-center gap-3 border-b border-white/5 text-sm', isActive(pathname, href) ? 'text-[#f4d58d]' : 'text-[#a9b8c9]')}>
                  <Icon className="h-4 w-4" />{label}<ChevronRight className="ml-auto h-4 w-4" />
                </Link>
              ))}
            </motion.nav>
          )}
        </AnimatePresence>
      </header>
      <nav className="fixed inset-x-3 bottom-3 z-50 grid grid-cols-5 rounded-2xl border border-white/10 bg-[#0a1728]/95 p-1.5 text-white shadow-2xl backdrop-blur-xl lg:hidden" aria-label="Mobile bottom navigation">
        {NAV_ITEMS.filter((item) => ['/', '/plan', '/chat', '/trips', '/settings'].includes(item.href) || item.label === 'Explore').slice(0, 5).map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} className={cn('flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl text-[10px]', isActive(pathname, href) ? 'bg-[#e7b75e] font-semibold text-[#07111f]' : 'text-[#9fafc0]')}>
            <Icon className="h-4 w-4" /><span>{label === 'Explore' ? 'Home' : label}</span>
          </Link>
        ))}
      </nav>
    </>
  );
}

export function PageFrame({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('min-h-screen bg-[#f5f1e8] text-[#152338]', className)}><TravelHeader />{children}</div>;
}

export function SectionHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: React.ReactNode }) {
  return <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div>{eyebrow && <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.22em] text-[#9a6b28]">{eyebrow}</p>}<h2 className="font-serif text-3xl font-semibold tracking-[-0.04em] text-[#152338] sm:text-4xl">{title}</h2>{description && <p className="mt-3 max-w-2xl text-[15px] leading-7 text-[#647185]">{description}</p>}</div>{action}</div>;
}

export function TrainCard({ recommended = false, compact = false, train = { name: 'Rajdhani Express', number: '12442', from: 'BSP', to: 'NDLS', departure: '18:40', arrival: '10:25', duration: '15h 45m', fare: '₹2,145', confirmation: '93%', delay: '88%', reliability: 'Excellent' } }: { recommended?: boolean; compact?: boolean; train?: { name: string; number: string; from: string; to: string; departure: string; arrival: string; duration: string; fare: string; confirmation: string; delay: string; reliability: string } }) {
  return <motion.article whileHover={{ y: -3 }} className={cn('relative overflow-hidden rounded-[22px] border bg-white shadow-[0_12px_35px_rgba(21,35,56,.07)]', recommended ? 'border-[#d2a851]' : 'border-[#e5dfd2]', compact ? 'p-4' : 'p-5 sm:p-6')}>
    {recommended && <div className="absolute right-0 top-0 rounded-bl-xl bg-[#e7b75e] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#07111f]">Best overall</div>}
    <div className="flex items-start justify-between gap-4"><div><p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[#9a6b28]">{train.number} · {train.reliability}</p><h3 className="mt-1 font-serif text-xl font-semibold text-[#152338]">{train.name}</h3></div><span className="rounded-full bg-[#edf5ef] px-2.5 py-1 text-xs font-semibold text-[#28714b]">{train.confirmation} confirm</span></div>
    <div className="my-5 grid grid-cols-[1fr_auto_1fr] items-center gap-3"><div><p className="text-2xl font-semibold tracking-tight text-[#152338]">{train.departure}</p><p className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-[#7d8898]">{train.from}</p></div><div className="flex flex-col items-center gap-1 text-[#a4acb8]"><span className="h-px w-14 bg-[#d8d4cc]" /><span className="text-[10px]">{train.duration}</span></div><div className="text-right"><p className="text-2xl font-semibold tracking-tight text-[#152338]">{train.arrival}</p><p className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-[#7d8898]">{train.to}</p></div></div>
    <div className="grid grid-cols-3 gap-2 border-t border-[#eee9df] pt-4 text-xs"><div><p className="text-[#8a94a3]">On-time confidence</p><p className="mt-1 font-semibold text-[#2e5f87]">{train.delay}</p></div><div><p className="text-[#8a94a3]">Fare from</p><p className="mt-1 font-semibold text-[#152338]">{train.fare}</p></div><div className="text-right"><p className="text-[#8a94a3]">Class</p><p className="mt-1 font-semibold text-[#152338]">3A · AC</p></div></div>
    {!compact && <div className="mt-5 flex items-center justify-between gap-3"><span className="flex items-center gap-1.5 text-xs text-[#6e7b8e]"><ShieldCheck className="h-4 w-4 text-[#28714b]" />Yatri verified route</span><Link href={`/search/${train.number}`} className="flex min-h-10 items-center gap-1 rounded-full bg-[#152338] px-4 text-xs font-semibold text-white transition hover:bg-[#254263]">View journey <ArrowRight className="h-3.5 w-3.5" /></Link></div>}
  </motion.article>;
}

export function AIThinking({ active = 2 }: { active?: number }) {
  const stages = ['Understanding your request', 'Searching trains', 'Analysing reliability', 'Finding alternatives'];
  return <div className="rounded-2xl border border-[#dfe5eb] bg-[#f8fbfd] p-4"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#152338]"><span className="grid h-7 w-7 place-items-center rounded-full bg-[#dcecf4] text-[#2e5f87]"><Sparkles className="h-3.5 w-3.5" /></span>Yatri is working</div><div className="grid gap-2 sm:grid-cols-2">{stages.map((stage, index) => <div key={stage} className="flex items-center gap-2 text-xs text-[#768397]"><span className={cn('grid h-5 w-5 place-items-center rounded-full border', index < active ? 'border-[#5c9b79] bg-[#e5f3ea] text-[#28714b]' : index === active ? 'border-[#d2a851] bg-[#fff4d9] text-[#9a6b28]' : 'border-[#d7dde4]')} >{index < active ? <Check className="h-3 w-3" /> : index === active ? <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" /> : null}</span>{stage}</div>)}</div></div>;
}

export function StatPill({ icon: Icon, label, value }: { icon: typeof Clock3; label: string; value: string }) {
  return <div className="flex items-center gap-2 rounded-full border border-[#e5dfd2] bg-white px-3 py-2 text-xs"><Icon className="h-3.5 w-3.5 text-[#9a6b28]" /><span className="text-[#7e8998]">{label}</span><strong className="text-[#152338]">{value}</strong></div>;
}

export function MiniJourney({ title, route, image, meta }: { title: string; route: string; image: string; meta: string }) {
  return <Link href="/plan" className="group relative block min-h-[200px] overflow-hidden rounded-[22px] text-white"><img src={image} alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-105" /><div className="absolute inset-0 bg-gradient-to-t from-[#07111f]/90 via-[#07111f]/25 to-transparent" /><div className="absolute inset-x-5 bottom-5"><p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#f4d58d]">{meta}</p><h3 className="mt-2 font-serif text-2xl font-semibold">{title}</h3><p className="mt-1 text-sm text-white/75">{route}</p></div></Link>;
}

export const iconSet = { Home, Search, Moon, CalendarDays, UserRound, Ticket, Bot };
