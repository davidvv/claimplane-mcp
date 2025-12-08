/**
 * Accessible Dropdown Menu Component with ARIA support
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

interface DropdownMenuProps {
  children: React.ReactNode;
}

interface DropdownMenuTriggerProps {
  asChild?: boolean;
  children: React.ReactNode;
}

interface DropdownMenuContentProps {
  align?: 'start' | 'center' | 'end';
  className?: string;
  children: React.ReactNode;
}

interface DropdownMenuItemProps {
  onClick?: () => void;
  className?: string;
  children: React.ReactNode;
}

interface DropdownMenuLabelProps {
  children: React.ReactNode;
}

const DropdownMenuContext = React.createContext<{
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  focusedIndex: number;
  setFocusedIndex: (index: number) => void;
  itemCount: number;
  setItemCount: (count: number) => void;
}>({
  isOpen: false,
  setIsOpen: () => {},
  focusedIndex: -1,
  setFocusedIndex: () => {},
  itemCount: 0,
  setItemCount: () => {},
});

export function DropdownMenu({ children }: DropdownMenuProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [focusedIndex, setFocusedIndex] = React.useState(-1);
  const [itemCount, setItemCount] = React.useState(0);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => setIsOpen(false);
    if (isOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isOpen]);

  // Reset focus when menu closes
  React.useEffect(() => {
    if (!isOpen) {
      setFocusedIndex(-1);
    }
  }, [isOpen]);

  return (
    <DropdownMenuContext.Provider
      value={{ isOpen, setIsOpen, focusedIndex, setFocusedIndex, itemCount, setItemCount }}
    >
      <div className="relative inline-block">{children}</div>
    </DropdownMenuContext.Provider>
  );
}

export function DropdownMenuTrigger({ asChild, children }: DropdownMenuTriggerProps) {
  const { isOpen, setIsOpen } = React.useContext(DropdownMenuContext);
  const triggerRef = React.useRef<HTMLButtonElement>(null);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setIsOpen(!isOpen);
    } else if (e.key === 'Escape' && isOpen) {
      setIsOpen(false);
      triggerRef.current?.focus();
    }
  };

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      ref: triggerRef,
      onClick: handleClick,
      onKeyDown: handleKeyDown,
      'aria-haspopup': 'true',
      'aria-expanded': isOpen,
    } as any);
  }

  return (
    <button
      ref={triggerRef}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-haspopup="true"
      aria-expanded={isOpen}
      type="button"
    >
      {children}
    </button>
  );
}

export function DropdownMenuContent({
  align = 'end',
  className,
  children,
}: DropdownMenuContentProps) {
  const { isOpen, setIsOpen, focusedIndex, setFocusedIndex, setItemCount } = React.useContext(DropdownMenuContext);
  const contentRef = React.useRef<HTMLDivElement>(null);

  // Count menu items
  React.useEffect(() => {
    if (contentRef.current) {
      const items = contentRef.current.querySelectorAll('[role="menuitem"]');
      setItemCount(items.length);
    }
  }, [children, setItemCount]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const itemsCount = contentRef.current?.querySelectorAll('[role="menuitem"]').length || 0;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedIndex((prev) => (prev + 1) % itemsCount);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedIndex((prev) => (prev - 1 + itemsCount) % itemsCount);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    } else if (e.key === 'Home') {
      e.preventDefault();
      setFocusedIndex(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setFocusedIndex(itemsCount - 1);
    }
  };

  if (!isOpen) return null;

  const alignmentClasses = {
    start: 'left-0',
    center: 'left-1/2 -translate-x-1/2',
    end: 'right-0',
  };

  return (
    <div
      ref={contentRef}
      role="menu"
      aria-orientation="vertical"
      className={cn(
        'absolute top-full mt-2 z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md',
        'animate-in fade-in-0 zoom-in-95',
        alignmentClasses[align],
        className
      )}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={handleKeyDown}
    >
      {children}
    </div>
  );
}

export function DropdownMenuItem({ onClick, className, children }: DropdownMenuItemProps) {
  const { setIsOpen, focusedIndex, setFocusedIndex } = React.useContext(DropdownMenuContext);
  const itemRef = React.useRef<HTMLButtonElement>(null);
  const [index, setIndex] = React.useState(-1);

  // Register index on mount
  React.useEffect(() => {
    if (itemRef.current) {
      const parent = itemRef.current.closest('[role="menu"]');
      if (parent) {
        const items = Array.from(parent.querySelectorAll('[role="menuitem"]'));
        const itemIndex = items.indexOf(itemRef.current);
        setIndex(itemIndex);
      }
    }
  }, []);

  // Focus management
  React.useEffect(() => {
    if (index === focusedIndex && itemRef.current) {
      itemRef.current.focus();
    }
  }, [focusedIndex, index]);

  const handleClick = () => {
    if (onClick) onClick();
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <button
      ref={itemRef}
      role="menuitem"
      tabIndex={-1}
      className={cn(
        'relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors text-left',
        'hover:bg-accent hover:text-accent-foreground',
        'focus:bg-accent focus:text-accent-foreground',
        className
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setFocusedIndex(index)}
    >
      {children}
    </button>
  );
}

export function DropdownMenuLabel({ children }: DropdownMenuLabelProps) {
  return <div className="px-2 py-1.5 text-sm font-semibold">{children}</div>;
}

export function DropdownMenuSeparator() {
  return <div className="my-1 h-px bg-muted" />;
}
