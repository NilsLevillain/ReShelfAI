import sprite from '@ds/icons.svg?raw';

export function IconSprite() {
  return <div hidden dangerouslySetInnerHTML={{ __html: sprite }} />;
}

export function Icon({ name, className = '' }: { name: string; className?: string }) {
  return (
    <svg className={`rs-icon ${className}`.trim()} aria-hidden="true">
      <use href={`#rs-i-${name}`} />
    </svg>
  );
}
