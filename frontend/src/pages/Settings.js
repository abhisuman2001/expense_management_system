import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Paper,
  Box,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Add, Edit, Delete } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { toast } from 'react-toastify';

const Settings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [categories, setCategories] = useState([]);
  const [openCategoryDialog, setOpenCategoryDialog] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [categoryForm, setCategoryForm] = useState({ name: '', description: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      console.log('Fetching settings data...');
      
      const [companyResponse, categoriesResponse] = await Promise.all([
        api.get('/company/info'),
        api.get('/company/categories'),
      ]);
      
      console.log('Company data:', companyResponse.data);
      console.log('Categories data:', categoriesResponse.data);
      
      setCompanyInfo(companyResponse.data.company);
      setCategories(categoriesResponse.data.categories);
    } catch (error) {
      console.error('Detailed error:', error);
      
      if (error.code === 'ECONNREFUSED') {
        toast.error('Cannot connect to server. Please ensure the backend is running.');
      } else if (error.response?.status === 401) {
        toast.error('Authentication failed. Please log in again.');
      } else {
        toast.error(error.response?.data?.message || 'Failed to fetch data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddCategory = () => {
    setCategoryForm({ name: '', description: '' });
    setEditingCategory(null);
    setOpenCategoryDialog(true);
  };

  const handleEditCategory = (category) => {
    setCategoryForm({ name: category.name, description: category.description });
    setEditingCategory(category);
    setOpenCategoryDialog(true);
  };

  const handleSaveCategory = async () => {
    try {
      if (!categoryForm.name.trim()) {
        toast.error('Category name is required');
        return;
      }

      if (editingCategory) {
        // Update existing category
        await api.put(`/company/categories/${editingCategory.id}`, categoryForm);
        toast.success('Category updated successfully');
      } else {
        // Create new category
        await api.post('/company/categories', categoryForm);
        toast.success('Category created successfully');
      }
      
      setOpenCategoryDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to save category');
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await api.delete(`/company/categories/${categoryId}`);
        toast.success('Category deleted successfully');
        fetchData();
      } catch (error) {
        toast.error(error.response?.data?.message || 'Failed to delete category');
      }
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        {/* Company Information */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Company Information
            </Typography>
            {companyInfo && (
              <Box>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Name:</strong> {companyInfo.name}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Country:</strong> {companyInfo.country}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Currency:</strong> {companyInfo.currency}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Total Employees:</strong> {companyInfo.total_employees}
                </Typography>
                <Typography variant="body1">
                  <strong>Total Managers:</strong> {companyInfo.total_managers}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* User Information */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Your Account
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              <strong>Name:</strong> {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              <strong>Email:</strong> {user?.email}
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              <strong>Role:</strong> 
              <Chip 
                label={user?.role?.toUpperCase()} 
                color="primary" 
                size="small" 
                sx={{ ml: 1 }}
              />
            </Typography>
          </Paper>
        </Grid>

        {/* Expense Categories Management */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Expense Categories
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleAddCategory}
              >
                Add Category
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {categories.map((category) => (
                    <TableRow key={category.id}>
                      <TableCell>{category.name}</TableCell>
                      <TableCell>{category.description}</TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          startIcon={<Edit />}
                          onClick={() => handleEditCategory(category)}
                          sx={{ mr: 1 }}
                        >
                          Edit
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<Delete />}
                          onClick={() => handleDeleteCategory(category.id)}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {categories.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No expense categories found. Add your first category to get started.
              </Alert>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Category Dialog */}
      <Dialog open={openCategoryDialog} onClose={() => setOpenCategoryDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingCategory ? 'Edit Category' : 'Add New Category'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Category Name"
            fullWidth
            variant="outlined"
            value={categoryForm.name}
            onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={categoryForm.description}
            onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCategoryDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveCategory} variant="contained">
            {editingCategory ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Settings;