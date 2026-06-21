"use client";

import dynamic from "next/dynamic";

const RouteMapInner = dynamic(() => import("./RouteMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[420px] items-center justify-center bg-slate-100 text-sm text-slate-500">
      Loading map…
    </div>
  ),
});

export default function RouteMap({ polyline, stops }) {
  return <RouteMapInner polyline={polyline} stops={stops} />;
}
