"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  src: string;
  poster: string;
  className?: string;
  loop?: boolean;
};

export function DemoVideo({ src, poster, className, loop = false }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(true);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => {
      setReduced(mq.matches);
      const v = ref.current;
      if (!v) return;
      if (mq.matches) {
        v.pause();
        setPlaying(false);
      }
    };
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  function toggle() {
    const v = ref.current;
    if (!v) return;
    if (v.paused) {
      void v.play();
      setPlaying(true);
    } else {
      v.pause();
      setPlaying(false);
    }
  }

  return (
    <div className={className} style={{ position: "relative" }}>
      <video
        ref={ref}
        src={src}
        poster={poster}
        muted
        playsInline
        autoPlay={!reduced}
        loop={loop && !reduced}
        preload="metadata"
        width={1920}
        height={1080}
        aria-label="Fly Swatter gameplay demo, muted"
      />
      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? "Pause video" : "Play video"}
        style={{
          position: "absolute",
          right: "0.75rem",
          bottom: "0.75rem",
          border: "1px solid rgba(244,239,228,0.2)",
          background: "rgba(7,16,24,0.75)",
          color: "#f4efe4",
          borderRadius: 999,
          padding: "0.45rem 0.8rem",
          fontFamily: "inherit",
          fontSize: "0.72rem",
          cursor: "pointer",
          touchAction: "manipulation",
        }}
      >
        {playing ? "pause" : "play"}
      </button>
    </div>
  );
}
