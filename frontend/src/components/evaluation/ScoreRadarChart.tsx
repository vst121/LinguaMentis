"use client";

import { useState } from "react";

export interface RadarDimension {
  key: string;
  label: string;
  score: number;
}

interface ScoreRadarChartProps {
  dimensions: RadarDimension[];
  accent?: "blue" | "emerald";
  ariaLabel?: string;
}

const ACCENT_STYLES = {
  blue: {
    fill: "rgba(37, 99, 235, 0.22)",
    stroke: "#2563eb",
    dot: "#1d4ed8",
    activeDot: "#1e3a8a",
    scoreText: "fill-blue-700",
  },
  emerald: {
    fill: "rgba(5, 150, 105, 0.22)",
    stroke: "#059669",
    dot: "#047857",
    activeDot: "#064e3b",
    scoreText: "fill-emerald-700",
  },
};

const GRID_LEVELS = [25, 50, 75, 100];

export function ScoreRadarChart({
  dimensions,
  accent = "blue",
  ariaLabel = "Bewertungs-Radar",
}: ScoreRadarChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const palette = ACCENT_STYLES[accent];

  if (dimensions.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        Noch keine Dimensionswerte vorhanden.
      </p>
    );
  }

  const width = 400;
  const height = 248;
  const cx = width / 2;
  const cy = 128;
  const radius = 70;
  const labelRadius = 86;

  // Use at least 5 radial grid spokes so the radar polygon remains legible even
  // when a partial/mock dataset has fewer than 3 dimensions.
  const spokeCount = Math.max(dimensions.length, 3);
  const angleForIndex = (idx: number, total: number) =>
    -Math.PI / 2 + (idx * 2 * Math.PI) / total;

  const pointAt = (angle: number, r: number) => ({
    x: cx + Math.cos(angle) * r,
    y: cy + Math.sin(angle) * r,
  });

  const gridPolygons = GRID_LEVELS.map((level) => {
    const r = (radius * level) / 100;
    const pts = Array.from({ length: spokeCount }, (_, i) => {
      const p = pointAt(angleForIndex(i, spokeCount), r);
      return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
    }).join(" ");
    return { level, points: pts };
  });

  const dataPoints = dimensions.map((dim, idx) => {
    const clamped = Math.max(0, Math.min(100, dim.score));
    const angle = angleForIndex(idx, dimensions.length);
    const pt = pointAt(angle, (radius * clamped) / 100);
    const axisEnd = pointAt(angle, radius);
    const labelPt = pointAt(angle, labelRadius);
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);

    let textAnchor: "start" | "middle" | "end" = "middle";
    if (cos > 0.25) textAnchor = "start";
    else if (cos < -0.25) textAnchor = "end";

    const labelYOffset = sin < -0.5 ? -8 : sin > 0.5 ? 10 : 0;

    return {
      ...dim,
      clamped,
      x: pt.x,
      y: pt.y,
      axisX: axisEnd.x,
      axisY: axisEnd.y,
      labelX: labelPt.x,
      labelY: labelPt.y + labelYOffset,
      textAnchor,
    };
  });

  const polygonPoints = dataPoints
    .map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  return (
    <div className="w-full" data-testid="score-radar-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="mx-auto h-auto w-full max-w-[380px] overflow-visible select-none"
        role="img"
        aria-label={ariaLabel}
      >
        {/* Concentric grid rings */}
        {gridPolygons.map(({ level, points }) => (
          <polygon
            key={level}
            points={points}
            fill={level === 100 ? "rgba(248, 250, 252, 0.7)" : "none"}
            stroke="#e2e8f0"
            strokeWidth={level === 100 ? 1.5 : 1}
            strokeDasharray={level === 100 ? undefined : "3 3"}
          />
        ))}

        {/* Grid ring numeric markers along the top axis */}
        {GRID_LEVELS.map((level) => (
          <text
            key={`lbl-${level}`}
            x={cx + 4}
            y={cy - (radius * level) / 100 + 3}
            className="fill-slate-400 text-[9px] font-medium"
          >
            {level}
          </text>
        ))}

        {/* Radial spoke lines */}
        {Array.from({ length: spokeCount }, (_, i) => {
          const end = pointAt(angleForIndex(i, spokeCount), radius);
          return (
            <line
              key={`spoke-${i}`}
              x1={cx}
              y1={cy}
              x2={end.x}
              y2={end.y}
              stroke="#e2e8f0"
              strokeWidth={1}
            />
          );
        })}

        {/* Score polygon (rendered when at least 3 axes exist; fallback line for 2) */}
        {dataPoints.length >= 3 ? (
          <polygon
            points={polygonPoints}
            fill={palette.fill}
            stroke={palette.stroke}
            strokeWidth={2.25}
            strokeLinejoin="round"
          />
        ) : dataPoints.length === 2 ? (
          <line
            x1={dataPoints[0].x}
            y1={dataPoints[0].y}
            x2={dataPoints[1].x}
            y2={dataPoints[1].y}
            stroke={palette.stroke}
            strokeWidth={2.25}
          />
        ) : null}

        {/* Data points and perimeter labels */}
        {dataPoints.map((p, idx) => {
          const isHovered = hoveredIdx === idx;
          const displayScore = Math.round(p.clamped * 10) / 10;
          return (
            <g
              key={p.key}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
              className="cursor-pointer"
            >
              <title>{`${p.label}: ${displayScore}`}</title>
              <circle
                cx={p.x}
                cy={p.y}
                r={isHovered ? 6 : 4.25}
                fill={isHovered ? palette.activeDot : palette.dot}
                stroke="#ffffff"
                strokeWidth={1.75}
              />
              <text
                x={p.labelX}
                y={p.labelY}
                textAnchor={p.textAnchor}
                className="fill-slate-700 text-[11px] font-semibold"
              >
                {p.label}
              </text>
              <text
                x={p.labelX}
                y={p.labelY + 13}
                textAnchor={p.textAnchor}
                className={`text-[11px] font-bold ${palette.scoreText}`}
              >
                {String(displayScore)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
