import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';

export default function ProtectedRoute({ user, requiredRole, children }) {
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== requiredRole && user.role !== "OPERATOR" && user.role !== "RESCUER") {
    return (
      <div className="max-w-md mx-auto my-12 p-6 panel-card border-rose-500/40 text-center">
        <ShieldAlert className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h3 className="font-heading font-bold text-base text-rose-300">Access Restricted</h3>
        <p className="text-xs text-slate-400 mt-1">
          This feed is restricted to pre-authorized emergency command operators and registered rescue units.
        </p>
      </div>
    );
  }

  return children;
}

