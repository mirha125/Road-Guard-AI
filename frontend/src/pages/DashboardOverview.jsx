import { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertTriangle, Video, Activity, MapPin, Trash2, Camera } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../context/AuthContext';

const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
        <div className={`p-3 rounded-lg ${color}`}>
            <Icon className="h-6 w-6 text-white" />
        </div>
        <div>
            <p className="text-sm text-gray-500 font-medium">{title}</p>
            <h3 className="text-2xl font-bold text-gray-800">{value}</h3>
        </div>
    </div>
);

const CameraCard = ({ camera }) => {
    const [isLive, setIsLive] = useState(false);
    const [hasError, setHasError] = useState(false);

    return (
        <div className="group relative bg-gray-900 rounded-lg overflow-hidden aspect-video shadow-md hover:shadow-xl transition-all duration-300">

            {camera.url ? (
                <div className="absolute inset-0">

                    <img
                        src={camera.url}
                        alt={camera.name}
                        className={`w-full h-full object-cover transition-opacity duration-500 ${isLive ? 'opacity-80 group-hover:opacity-100' : 'opacity-0'}`}
                        onLoad={() => { setIsLive(true); setHasError(false); }}
                        onError={(e) => {
                            setIsLive(false);
                            setHasError(true);
                        }}
                    />


                    {(!isLive || hasError) && (
                        <img
                            src='https://placehold.co/600x400/1f2937/ffffff?text=No+Signal'
                            alt="No Signal"
                            className="w-full h-full object-cover absolute inset-0"
                        />
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent"></div>
                </div>
            ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
                    <Camera className="h-10 w-10 text-gray-600" />
                </div>
            )}

            {/* AI Monitoring Badge */}
            {camera.detection_active && (
                <div className="absolute top-2 left-2 z-10">
                    <span className="px-1.5 py-0.5 bg-green-500 text-white text-[10px] font-bold rounded flex items-center shadow-sm animate-pulse">
                        <Activity className="h-3 w-3 mr-1" />
                        AI ON
                    </span>
                </div>
            )}

            <div className="absolute inset-0 p-3 flex flex-col justify-between z-10">
                <div className="flex justify-end">
                    {isLive && !hasError ? (
                        <span className="px-1.5 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded flex items-center animate-pulse">
                            <span className="w-1.5 h-1.5 bg-white rounded-full mr-1"></span>
                            LIVE
                        </span>
                    ) : (
                        <span className="px-1.5 py-0.5 bg-gray-700 text-gray-300 text-[10px] font-bold rounded flex items-center">
                            OFFLINE
                        </span>
                    )}
                </div>

                <div>
                    <p className="text-white text-sm font-medium truncate shadow-sm">
                        {camera.name}
                    </p>
                    <p className="text-gray-300 text-xs truncate flex items-center mt-0.5">
                        <MapPin className="h-3 w-3 mr-1" />
                        {camera.location}
                    </p>
                </div>
            </div>
        </div>
    );
};

const DashboardOverview = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState({
        alerts: 0,
        activeStreams: 0,
        cameras: 0,
        users: 0
    });
    const [recentAlerts, setRecentAlerts] = useState([]);
    const [allAlerts, setAllAlerts] = useState([]);
    const [cameras, setCameras] = useState([]);
    const [streams, setStreams] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [timeRange, setTimeRange] = useState('24h');

    const processChartData = (alerts, range) => {
        const now = new Date();
        let buckets = [];
        let startTime;

        switch (range) {
            case '24h':
                buckets = [
                    { time: '00:00', count: 0 },
                    { time: '04:00', count: 0 },
                    { time: '08:00', count: 0 },
                    { time: '12:00', count: 0 },
                    { time: '16:00', count: 0 },
                    { time: '20:00', count: 0 }
                ];
                startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const hour = alertTime.getHours();
                        const bucketIndex = Math.floor(hour / 4);
                        buckets[bucketIndex].count++;
                    }
                });
                break;

            case '7d':
                for (let i = 6; i >= 0; i--) {
                    const date = new Date(now);
                    date.setDate(date.getDate() - i);
                    buckets.push({
                        time: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                        count: 0
                    });
                }
                startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const daysDiff = Math.floor((now - alertTime) / (24 * 60 * 60 * 1000));
                        const bucketIndex = 6 - daysDiff;
                        if (bucketIndex >= 0 && bucketIndex < 7) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case '30d':
                for (let i = 4; i >= 0; i--) {
                    buckets.push({
                        time: `Week ${5 - i}`,
                        count: 0
                    });
                }
                startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const weeksDiff = Math.floor((now - alertTime) / (7 * 24 * 60 * 60 * 1000));
                        const bucketIndex = 4 - weeksDiff;
                        if (bucketIndex >= 0 && bucketIndex < 5) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case '1y':
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                for (let i = 11; i >= 0; i--) {
                    const monthDate = new Date(now);
                    monthDate.setMonth(monthDate.getMonth() - i);
                    buckets.push({
                        time: months[monthDate.getMonth()],
                        count: 0
                    });
                }
                startTime = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const monthsDiff = (now.getFullYear() - alertTime.getFullYear()) * 12 +
                            (now.getMonth() - alertTime.getMonth());
                        const bucketIndex = 11 - monthsDiff;
                        if (bucketIndex >= 0 && bucketIndex < 12) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case 'all':
                const alertsByMonth = {};
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    const monthKey = `${alertTime.getFullYear()}-${String(alertTime.getMonth() + 1).padStart(2, '0')}`;
                    alertsByMonth[monthKey] = (alertsByMonth[monthKey] || 0) + 1;
                });

                const sortedMonths = Object.keys(alertsByMonth).sort();
                buckets = sortedMonths.map(monthKey => {
                    const [year, month] = monthKey.split('-');
                    const date = new Date(year, month - 1);
                    return {
                        time: date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
                        count: alertsByMonth[monthKey]
                    };
                });
                break;
        }

        return buckets;
    };

    const fetchData = async () => {
        try {
            const [alertsRes, streamsRes, camerasRes, usersRes] = await Promise.all([
                axios.get('http://localhost:8000/alerts/'),
                axios.get('http://localhost:8000/streams/'),
                axios.get('http://localhost:8000/cameras/'),
                axios.get('http://localhost:8000/users/')
            ]);

            setStats({
                alerts: alertsRes.data.length,
                activeStreams: streamsRes.data.filter(s => s.is_active).length,
                cameras: camerasRes.data.length,
                users: usersRes.data.length
            });
            setRecentAlerts(alertsRes.data.slice(0, 5));
            setAllAlerts(alertsRes.data);
            setCameras(camerasRes.data);
            setStreams(streamsRes.data);
            setChartData(processChartData(alertsRes.data, timeRange));
        } catch (error) {
            console.error("Error fetching dashboard data", error);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (allAlerts.length > 0) {
            setChartData(processChartData(allAlerts, timeRange));
        }
    }, [timeRange, allAlerts]);

    const handleDeleteAlert = async (id) => {
        if (!confirm("Are you sure you want to delete this alert?")) return;
        try {
            await axios.delete(`http://localhost:8000/alerts/${id}`);
            fetchData();
        } catch (error) {
            console.error("Error deleting alert", error);
            alert("Failed to delete alert");
        }
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                    <p className="text-sm font-medium text-gray-800">{payload[0].payload.time}</p>
                    <p className="text-sm text-red-600">
                        accidents: <span className="font-bold">{payload[0].value}</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    const getChartTitle = () => {
        switch (timeRange) {
            case '24h': return 'Accident Trends (24h)';
            case '7d': return 'Accident Trends (7 Days)';
            case '30d': return 'Accident Trends (30 Days)';
            case '1y': return 'Accident Trends (1 Year)';
            case 'all': return 'Accident Trends (All Time)';
            default: return 'Accident Trends';
        }
    };

    return (
        <div className="p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Overview</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard title="Total Alerts" value={stats.alerts} icon={AlertTriangle} color="bg-red-500" />
                <StatCard title="Cameras" value={stats.cameras} icon={Video} color="bg-blue-500" />
                <StatCard title="Total Users" value={stats.users} icon={MapPin} color="bg-purple-500" />
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-8">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-gray-800">{getChartTitle()}</h3>
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value)}
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="1y">Last 1 Year</option>
                        <option value="all">All Time</option>
                    </select>
                </div>
                <div className="p-6">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: '#e5e7eb' }} />
                            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: '#e5e7eb' }} />
                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(239, 68, 68, 0.1)' }} />
                            <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} maxBarSize={60} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-8">
                <div className="p-6 border-b border-gray-100">
                    <h3 className="text-lg font-bold text-gray-800">Recent Alerts</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 text-gray-600 font-medium text-sm">
                            <tr>
                                <th className="px-6 py-3">Location</th>
                                <th className="px-6 py-3">Time</th>
                                <th className="px-6 py-3">Details</th>
                                <th className="px-6 py-3">Status</th>
                                {user?.role === 'admin' && <th className="px-6 py-3">Actions</th>}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {recentAlerts.map((alert) => (
                                <tr key={alert._id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-800">{alert.location}</td>
                                    <td className="px-6 py-4 text-gray-500">{new Date(alert.time).toLocaleString()}</td>
                                    <td className="px-6 py-4 text-gray-600">{alert.details}</td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                            Critical
                                        </span>
                                    </td>
                                    {user?.role === 'admin' && (
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => handleDeleteAlert(alert._id)}
                                                className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                                                title="Delete Alert"
                                            >
                                                <Trash2 className="h-5 w-5" />
                                            </button>
                                        </td>
                                    )}
                                </tr>
                            ))}
                            {recentAlerts.length === 0 && (
                                <tr>
                                    <td colSpan={user?.role === 'admin' ? "5" : "4"} className="px-6 py-8 text-center text-gray-500">
                                        No alerts generated yet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>


            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center">
                        <Camera className="h-5 w-5 mr-2" />
                        All Cameras ({cameras.length})
                    </h3>
                </div>
                <div className="p-6">
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                        {cameras.map((camera) => (
                            <CameraCard key={camera._id} camera={camera} />
                        ))}

                        {cameras.length === 0 && (
                            <div className="col-span-full text-center py-12 text-gray-500">
                                <Camera className="h-12 w-12 mx-auto mb-3 opacity-30" />
                                <p>No cameras available</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardOverview;
