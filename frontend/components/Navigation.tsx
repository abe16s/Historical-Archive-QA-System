'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Chat' },
    { href: '/documents', label: 'Documents' },
    { href: '/upload', label: 'Upload' },
    { href: '/evaluation', label: 'Evaluation' },
  ];

  return (
    <nav className="bg-white border-b border-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex-shrink-0 flex items-center">
            <h1 className="text-xl font-bold text-black">
              Historical Archive QA
            </h1>
          </div>
          <div className="hidden sm:flex sm:space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  pathname === item.href
                    ? 'border-black text-black'
                    : 'border-transparent text-gray-600 hover:text-black hover:border-gray-400'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}

