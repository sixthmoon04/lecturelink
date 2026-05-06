import React from 'react';

const paths = {
  Menu: [
    ['path', { d: 'M4 6h16M4 12h16M4 18h16' }],
  ],
  X: [
    ['path', { d: 'M18 6 6 18M6 6l12 12' }],
  ],
  ArrowRight: [
    ['path', { d: 'M5 12h14M13 5l7 7-7 7' }],
  ],
  Check: [
    ['path', { d: 'm5 12 4 4L19 6' }],
  ],
  Sparkles: [
    ['path', { d: 'm12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z' }],
    ['path', { d: 'm18 15 .8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8L18 15Z' }],
  ],
  Brain: [
    ['path', { d: 'M9 4a3 3 0 0 0-3 3v1a4 4 0 0 0 0 8v1a3 3 0 0 0 5 2.2' }],
    ['path', { d: 'M15 4a3 3 0 0 1 3 3v1a4 4 0 0 1 0 8v1a3 3 0 0 1-5 2.2' }],
    ['path', { d: 'M12 5v14M8 9h3M13 9h3M8 15h3M13 15h3' }],
  ],
  FileText: [
    ['path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z' }],
    ['path', { d: 'M14 2v6h6M8 13h8M8 17h8M8 9h2' }],
  ],
  Target: [
    ['circle', { cx: '12', cy: '12', r: '9' }],
    ['circle', { cx: '12', cy: '12', r: '5' }],
    ['circle', { cx: '12', cy: '12', r: '1.5' }],
  ],
  Shield: [
    ['path', { d: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z' }],
  ],
  Zap: [
    ['path', { d: 'M13 2 4 14h7l-1 8 10-13h-7l0-7Z' }],
  ],
  ChevronRight: [
    ['path', { d: 'm9 18 6-6-6-6' }],
  ],
  Link2: [
    ['path', { d: 'M9 17H7a5 5 0 0 1 0-10h2' }],
    ['path', { d: 'M15 7h2a5 5 0 0 1 0 10h-2' }],
    ['path', { d: 'M8 12h8' }],
  ],
  Stethoscope: [
    ['path', { d: 'M6 3v5a4 4 0 0 0 8 0V3' }],
    ['path', { d: 'M10 12v3a5 5 0 0 0 10 0v-2' }],
    ['circle', { cx: '20', cy: '10', r: '2' }],
  ],
  Search: [
    ['circle', { cx: '11', cy: '11', r: '7' }],
    ['path', { d: 'm20 20-4-4' }],
  ],
  AlertTriangle: [
    ['path', { d: 'M10.3 3.9 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z' }],
    ['path', { d: 'M12 9v4M12 17h.01' }],
  ],
};

function makeIcon(name) {
  return function Icon({ size = 24, color = 'currentColor', strokeWidth = 2, className = '', ...props }) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        aria-hidden="true"
        {...props}
      >
        {(paths[name] || []).map(([Tag, attrs], idx) => <Tag key={idx} {...attrs} />)}
      </svg>
    );
  };
}

export const Menu = makeIcon('Menu');
export const X = makeIcon('X');
export const ArrowRight = makeIcon('ArrowRight');
export const Check = makeIcon('Check');
export const Sparkles = makeIcon('Sparkles');
export const Brain = makeIcon('Brain');
export const FileText = makeIcon('FileText');
export const Target = makeIcon('Target');
export const Shield = makeIcon('Shield');
export const Zap = makeIcon('Zap');
export const ChevronRight = makeIcon('ChevronRight');
export const Link2 = makeIcon('Link2');
export const Stethoscope = makeIcon('Stethoscope');
export const Search = makeIcon('Search');
export const AlertTriangle = makeIcon('AlertTriangle');
