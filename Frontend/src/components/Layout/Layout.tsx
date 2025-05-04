import { ReactNode, useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(location.pathname);
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navbarRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 700px)");
    const updateNavbar = (e: MediaQueryListEvent | MediaQueryList) => {
      setIsMobile(e.matches);
    };

    // Initial check
    updateNavbar(media);

    // Add listener for changes
    media.addEventListener('change', updateNavbar);

    // Cleanup
    return () => media.removeEventListener('change', updateNavbar);
  }, []);

  // Apply inert property using useEffect since it's not a standard React prop
  useEffect(() => {
    if (navbarRef.current) {
      if (isMobile && !sidebarOpen) {
        navbarRef.current.setAttribute('inert', '');
      } else {
        navbarRef.current.removeAttribute('inert');
      }
    }
  }, [isMobile, sidebarOpen]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleTabChange = (path: string) => {
    setActiveTab(path);
    navigate(path);
    if (isMobile) {
      closeSidebar();
    }
  };

  const openSidebar = () => {
    setSidebarOpen(true);
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  const tabs = [
    { path: '/dashboard', label: 'Devices' },
    { path: '/users', label: 'User Management' },
    { path: '/statistics', label: 'Statistics' },
    { path: '/profile', label: 'Profile' }
  ];

  return (
    <div className="admin-layout">
      <button
        id="open-sidebar-button"
        onClick={openSidebar}
        aria-expanded={sidebarOpen}
        aria-label="open menu"
        style={{ display: isMobile ? 'block' : 'none' }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#c9c9c9">
          <path d="M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z" />
        </svg>
      </button>

      <nav
        ref={navbarRef}
        id="navbar"
        className={sidebarOpen ? 'show' : ''}
        aria-label="Main navigation"
      >
        <ul>
          <li style={{ display: isMobile ? 'block' : 'none' }}>
            <button
              id="close-sidebar-button"
              onClick={closeSidebar}
              aria-label="close sidebar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#c9c9c9">
                <path d="m480-444.62-209.69 209.7q-7.23 7.23-17.5 7.42-10.27.19-17.89-7.42-7.61-7.62-7.61-17.7 0-10.07 7.61-17.69L444.62-480l-209.7-209.69q-7.23-7.23-7.42-17.5-.19-10.27 7.42-17.89 7.62-7.61 17.7-7.61 10.07 0 17.69 7.61L480-515.38l209.69-209.7q7.23-7.23 17.5-7.42 10.27-.19 17.89 7.42 7.61 7.62 7.61 17.7 0 10.07-7.61 17.69L515.38-480l209.7 209.69q7.23 7.23 7.42 17.5.19 10.27-7.42 17.89-7.62 7.61-17.7 7.61-10.07 0-17.69-7.61L480-444.62Z" />
              </svg>
            </button>
          </li>

          {tabs.map(tab => (
            <li key={tab.path}>
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); handleTabChange(tab.path); }}
                className={activeTab === tab.path ? 'active-link' : ''}
                aria-current={activeTab === tab.path ? 'page' : undefined}
              >
                {tab.label}
              </a>
            </li>
          ))}
          <li>
            <a
              href="#"
              className="logout-link"
              onClick={(e) => { e.preventDefault(); handleLogout(); }}
            >
              Logout
            </a>
          </li>
        </ul>
      </nav>

      <div
        id="overlay"
        onClick={closeSidebar}
        aria-hidden="true"
        style={{ display: sidebarOpen ? 'block' : 'none' }}
      ></div>

      <main id="main-content" className="content">
        <div className="centered-container">
          {children}
        </div>
      </main>
    </div>
  );
}
