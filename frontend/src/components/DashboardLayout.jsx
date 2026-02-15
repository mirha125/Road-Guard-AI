import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Users, Video, AlertTriangle, LogOut, History, Shield } from 'lucide-react';

const DashboardLayout = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path) => location.pathname === path;

    const NavItem = ({ to, icon: Icon, label }) => (
        <Link
            to={to}
            className={`flex items-center space-x-3 px-6 py-3 transition-colors duration-200 ${isActive(to)
                ? 'bg-blue-600 text-white border-r-4 border-blue-300'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
        >
            <Icon className="h-5 w-5" />
            <span className="font-medium">{label}</span>
        </Link>
    );

    return (
        <div className="flex h-screen bg-gray-100">

            <div className="w-64 bg-gray-900 text-white flex flex-col shadow-xl z-10">
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center space-x-2">
                        <Shield className="h-8 w-8 text-blue-400" />
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                            RoadGuard
                        </h1>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Safety Monitoring System</p>
                </div>

                <nav className="flex-1 mt-6">
                    <NavItem to="/dashboard" icon={LayoutDashboard} label="Overview" />
                    <NavItem to="/dashboard/feeds" icon={Video} label="Cameras" />
                    <NavItem to="/dashboard/history" icon={History} label="Stream History" />

                    {user?.role === 'admin' && (
                        <NavItem to="/dashboard/admin" icon={Users} label="Admin Panel" />
                    )}
                </nav>

                <div className="p-4 border-t border-gray-800">
                    <div className="flex items-center mb-4 px-2">
                        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold">
                            {user?.email?.[0].toUpperCase()}
                        </div>
                        <div className="ml-3">
                            <p className="text-sm font-medium text-white truncate w-32">{user?.email}</p>
                            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg transition-colors text-sm font-medium"
                    >
                        <LogOut className="h-4 w-4" />
                        <span>Sign Out</span>
                    </button>
                </div>
            </div>


            <div className="flex-1 overflow-auto">
                <Outlet />
            </div>
        </div>
    );
};

export default DashboardLayout;
