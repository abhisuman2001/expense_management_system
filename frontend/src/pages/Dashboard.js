import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
} from '@mui/material';
import {
  Receipt,
  Pending,
  CheckCircle,
  Cancel,
  TrendingUp,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [expensesResponse, approvalsResponse] = await Promise.all([
        api.get('/expenses'),
        user.role !== 'employee' ? api.get('/approvals/pending') : Promise.resolve({ data: { approvals: [] } }),
      ]);

      const expenses = expensesResponse.data.expenses;
      const pendingApprovals = approvalsResponse.data.approvals;

      // Calculate statistics
      const stats = {
        totalExpenses: expenses.length,
        pendingExpenses: expenses.filter(e => e.status === 'pending').length,
        approvedExpenses: expenses.filter(e => e.status === 'approved').length,
        rejectedExpenses: expenses.filter(e => e.status === 'rejected').length,
        totalAmount: expenses.reduce((sum, e) => sum + parseFloat(e.amount_in_company_currency), 0),
        pendingApprovals: pendingApprovals.length,
        recentExpenses: expenses.slice(0, 5),
      };

      setDashboardData(stats);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" component="div" color={color}>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
          <Box color={color}>{icon}</Box>
        </Box>
      </CardContent>
    </Card>
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.first_name}!
      </Typography>
      
      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Expenses"
            value={dashboardData?.totalExpenses || 0}
            icon={<Receipt fontSize="large" />}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Expenses"
            value={dashboardData?.pendingExpenses || 0}
            icon={<Pending fontSize="large" />}
            color="warning"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Approved Expenses"
            value={dashboardData?.approvedExpenses || 0}
            icon={<CheckCircle fontSize="large" />}
            color="success"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Amount"
            value={`${user?.company_currency} ${dashboardData?.totalAmount?.toFixed(2) || '0.00'}`}
            icon={<TrendingUp fontSize="large" />}
            color="primary"
          />
        </Grid>

        {/* Pending Approvals (for Managers/Admins) */}
        {user?.role !== 'employee' && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Pending Approvals</Typography>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/approvals')}
                  disabled={!dashboardData?.pendingApprovals}
                >
                  View All
                </Button>
              </Box>
              
              {dashboardData?.pendingApprovals > 0 ? (
                <Typography variant="h4" color="warning.main">
                  {dashboardData.pendingApprovals}
                </Typography>
              ) : (
                <Typography color="text.secondary">
                  No pending approvals
                </Typography>
              )}
            </Paper>
          </Grid>
        )}

        {/* Recent Expenses */}
        <Grid item xs={12} md={user?.role === 'employee' ? 12 : 6}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Recent Expenses</Typography>
              <Button
                variant="outlined"
                onClick={() => navigate('/expenses')}
              >
                View All
              </Button>
            </Box>
            
            {dashboardData?.recentExpenses?.length > 0 ? (
              <Box>
                {dashboardData.recentExpenses.map((expense) => (
                  <Box
                    key={expense.id}
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                    py={1}
                    borderBottom="1px solid #eee"
                  >
                    <Box>
                      <Typography variant="body1">
                        {expense.description}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {expense.category} • {expense.expense_date}
                      </Typography>
                    </Box>
                    <Box textAlign="right">
                      <Typography variant="body1" fontWeight="bold">
                        {expense.currency} {expense.amount}
                      </Typography>
                      <Chip
                        label={expense.status}
                        color={getStatusColor(expense.status)}
                        size="small"
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography color="text.secondary">
                No expenses found
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Button
                variant="contained"
                startIcon={<Receipt />}
                onClick={() => navigate('/submit-expense')}
              >
                Submit New Expense
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => navigate('/expenses')}
              >
                View My Expenses
              </Button>
              
              {user?.role !== 'employee' && (
                <Button
                  variant="outlined"
                  onClick={() => navigate('/approvals')}
                >
                  Review Approvals
                </Button>
              )}
              
              {user?.role === 'admin' && (
                <Button
                  variant="outlined"
                  onClick={() => navigate('/users')}
                >
                  Manage Users
                </Button>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;