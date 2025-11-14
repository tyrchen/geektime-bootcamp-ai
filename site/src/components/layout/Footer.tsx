import { Github, Twitter, Mail } from 'lucide-react';
import { getUrl } from '../../utils/url';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    课程: [
      { label: '课程大纲', href: '/curriculum' },
      { label: '工具生态', href: '/tools' },
      { label: '实战项目', href: '/projects' },
      { label: '学习资料', href: '/materials' },
    ],
    资料: [
      { label: 'Claude Code 架构', href: '/materials/claude-code-architecture' },
      { label: '工具对比', href: '/materials/ai-coding-tools-comparison' },
      { label: 'NotebookLM', href: '/materials/notebooklm-guide' },
    ],
    关于: [
      { label: '课程价值', href: '/about#value' },
      { label: '适合人群', href: '/about#audience' },
      { label: '讲师介绍', href: '/about#instructor' },
    ],
  };

  const socialLinks = [
    { icon: Github, href: 'https://github.com', label: 'GitHub' },
    { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
    { icon: Mail, href: 'mailto:contact@example.com', label: 'Email' },
  ];

  return (
    <footer className="bg-bg-secondary border-t border-gray-200">
      <div className="container-custom py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <h3 className="text-xl font-semibold text-primary mb-4">
              陈天 AI 训练营
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              让 AI 成为你的编程超能力
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-sm font-semibold text-primary mb-4">
                {category}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.href}>
                    <a
                      href={getUrl(link.href)}
                      className="text-sm text-text-secondary hover:text-accent transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-text-secondary">
            © {currentYear} 陈天极客时间 AI 训练营. All rights reserved.
          </p>

          {/* Social Links */}
          <div className="flex items-center gap-6">
            {socialLinks.map((social) => {
              const Icon = social.icon;
              return (
                <a
                  key={social.label}
                  href={social.href}
                  className="text-text-secondary hover:text-accent transition-colors"
                  aria-label={social.label}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Icon size={20} />
                </a>
              );
            })}
          </div>
        </div>
      </div>
    </footer>
  );
}
