import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
import scipy
import matplotlib.pyplot as plt
from IPython.display import clear_output
import pulp
from sklearn.decomposition import TruncatedSVD

import sys
import atexit
from pyaedt import *
import pyaedt
import subprocess
import psutil
import shutil
from datetime import datetime
import numpy as np
import pandas as pd
from pyaedt.application.Variables import Variable
from scipy.stats import qmc,norm,multivariate_normal

import os
import shutil
from datetime import datetime

import joblib

from sklearn.tree import ExtraTreeRegressor,DecisionTreeRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import KernelDensity

from sklearn.decomposition import PCA
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

import logging
from time import sleep


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.nn import functional as F
from sklearn.preprocessing import MinMaxScaler
import math

from sklearn.metrics.pairwise import euclidean_distances
from scipy.optimize import Bounds,LinearConstraint,NonlinearConstraint,minimize

import optuna

from fastdtw import fastdtw
from sklearn.manifold import MDS

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from sklearn.linear_model import MultiTaskLasso,MultiTaskLassoCV,LinearRegression
# from lineartree import LinearTreeRegressor

# import lightgbm
from sklearn.multioutput import MultiOutputRegressor

PARAM_NAMES_CODE2DATA = {
    "h_subs":"height of substrate",
    "l_patch":"length of patch",
    "w_patch":"width of patch",
    "h_patch":"height of patch",
    "h_sr":"height of solder resist layer",
    "r_probe":"radius of the probe",
    "c_pad":"c_pad",
    "c_antipad":"c_antipad",
    "c_probe":"c_probe",
    "$e1":"dielectric constant of substrate",
    "$e2":"dielectric constant of solder resist layer",
}

PARAM_NAMES_DATA2CODE = {v:k for k,v in PARAM_NAMES_CODE2DATA.items()}

PARAM_UNITS_DICT = {'h_subs': 'mm','l_patch': 'mm','w_patch': 'mm',
                    'h_patch': 'mm','h_sr': 'mm','r_probe': 'mm',
                    'c_pad': 'mm','c_antipad': 'mm','c_probe': '',
                    '$e2': '','$e1': '','r_pad': 'mm','r_antipad': 'mm',
                    'd_probe': 'mm'}

INPUT_LIMITS = {'length of patch': {'min': 1.8, 'max': 5.2},
 'width of patch': {'min': 1.8, 'max': 5.2},
 'height of patch': {'min': 0.01, 'max': 0.04},
 'height of substrate': {'min': 0.1, 'max': 0.8},
 'height of solder resist layer': {'min': 0.02, 'max': 0.1},
 'radius of the probe': {'min': 0.015, 'max': 0.05},
 'c_pad': {'min': 0.0, 'max': 0.025},
 'c_antipad': {'min': 0.025, 'max': 0.1},
 'c_probe': {'min': 0.05, 'max': 0.45},
 'dielectric constant of substrate': {'min': 2.0, 'max': 5.0},
 'dielectric constant of solder resist layer': {'min': 2.0, 'max': 5.0}}

INPUT_LIMITS_NP = pd.DataFrame(INPUT_LIMITS).values

EXCEL_COLUMN_ORDER = ['length of patch', 'width of patch', 'height of patch',
       'height of substrate', 'height of solder resist layer',
       'radius of the probe', 'c_pad', 'c_antipad', 'c_probe',
       'dielectric constant of substrate',
       'dielectric constant of solder resist layer']

INPUT_MIN = INPUT_LIMITS_NP[0]
INPUT_MAX = INPUT_LIMITS_NP[1]
INPUT_RANGE = INPUT_MAX - INPUT_MIN

def dtw_matrix(time_series_list):
    num_series = len(time_series_list)
    distance_matrix = np.zeros((num_series, num_series))

    for i in range(num_series):
        for j in range(i + 1, num_series):  # Optimize for symmetry
            distance, _ = fastdtw(time_series_list[i], time_series_list[j])
            distance_matrix[i, j] = distance
            distance_matrix[j, i] = distance  # Distance matrix is symmetric

    return np.array(distance_matrix)






def convert_to_dtw_coordinates(data,n_components = 15):
    dist_mat = dtw_matrix(data)
    mds = MDS(n_components=n_components, dissimilarity='precomputed',random_state=0)  # 2D coordinates
    coordinates = mds.fit_transform(dist_mat)
    return coordinates


class AEDT_session():
    def __init__(self):
        pass

    def start_new_desktop(self):
        self.desktop = Desktop()
        self.desktop_id = self.desktop.aedt_process_id
    

    def kill_process_by_name(self,process_name='ansysedt.exe'):
        """
        Kill a process by its name. Coded to terminate errored Ansys application.

        Args:
            process_name (str): Name of the process to be terminated (default is 'ansysedt.exe').
        """
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'] == process_name:
                sleep(15)
                psutil.Process(proc.info['pid']).terminate()
                print(f'Process {process_name} has been killed')

    def do_hfss(self,original_filepath,new_filepath,variable_values_dict,
        output_folder=None,file_suffix=None,counter=0):
        try:
            shutil.copy(original_filepath,new_filepath)
            log_filepath = new_filepath.split(".aedt")[0]+"_hfss.log"
            create_logger(log_filepath)

            # desktop = Desktop()
            
            hfss = Hfss(new_filepath,aedt_process_id=self.desktop_id)
            self.change_hfss_variables(hfss,variable_values_dict)
            varMan = hfss.variable_manager
            print({e:varMan.variables[e].numeric_value for e in varMan.variable_names})
            return self.analyze_hfss(hfss,output_folder,file_suffix)
        except:
            if counter < 100:
                sleep(counter*60)
                try:
                    psutil.Process(self.desktop.aedt_process_id).kill()
                except:
                    print("Couldn't kill PID.")
                new_sg_file_folder = "/".join(new_filepath.split("/")[:-1])
                
                new_sg_file_paths = [new_sg_file_folder+"/"+e for e in os.listdir(new_sg_file_folder) 
                    if e.startswith(new_filepath.split("/")[-1].replace(".aedt",""))]
                for f in new_sg_file_paths:
                    if "hfss.log" not in f:
                        try:
                            os.remove(f)
                        except:
                            print(f"Couldn't remove {f}")
                del self.desktop
                self.start_new_desktop()
                return self.do_hfss(original_filepath,new_filepath,variable_values_dict,output_folder,file_suffix,counter+1)

    def change_hfss_variables(self,hfss,variable_values_dict):
        varMan = hfss.variable_manager
        for k,v in variable_values_dict.items():
            varMan.set_variable(k,expression = f"{v}{PARAM_UNITS_DICT[k]}")
        hfss.save_project()

    def analyze_hfss(self,hfss,output_folder,file_suffix):
        varMan = hfss.variable_manager
        inputs_pd = pd.DataFrame({e:[varMan[e].numeric_value] for e in varMan.variable_names})
        inputs_pd.columns = inputs_pd.columns.map(PARAM_NAMES_CODE2DATA)
        inputs_pd[EXCEL_COLUMN_ORDER]
        if output_folder:
            inputs_pd.to_csv(f"{output_folder}/inputs_{file_suffix}.csv")

        hfss.analyze()
        hfss.save_project()
        var_name = hfss.get_traces_for_plot(category="S")
        sol_data = hfss.post.get_solution_data(var_name)
        real_part = list(sol_data._solutions_real[var_name[0]].values())
        imag_part = list(sol_data._solutions_imag[var_name[0]].values())
        real_part = np.array(real_part)
        imag_part =  np.array(imag_part)
        mag_part = (real_part**2+imag_part**2)**.5
        if output_folder:
            pd.DataFrame({"real":real_part,"imag":imag_part}).to_csv(
                f"{output_folder}/outputs_{file_suffix}.csv")
        hfss.close_project()
        return real_part,imag_part,mag_part

def emulate_nn(test_parameters,output_folder=None,file_suffix=None):
    nn_columns_ordered = np.array(['length of patch', 'width of patch', 'height of patch',
       'height of substrate', 'height of solder resist layer',
       'radius of the probe', 'c_pad', 'c_antipad', 'c_probe',
       'dielectric constant of substrate',
       'dielectric constant of solder resist layer'])
    nn_columns_ordered_code = np.array([PARAM_NAMES_DATA2CODE[e] for e in nn_columns_ordered])
    model = NeuralNet()#.to(device="cpu")
    model.load_state_dict(torch.load("NNModel/trained_model.pt"))
    scaler = joblib.load("NNModel/scaler.gz")

    x = pd.DataFrame({k:[v] for k,v in test_parameters.items()})
    x.columns = np.array([PARAM_NAMES_CODE2DATA[e] for e in x.columns])
    
    if output_folder is not None:
        x.to_csv(f"{output_folder}/inputs_{file_suffix}.csv")
    x_scaled = scaler.transform(x)
    y = model(torch.tensor(x_scaled).float()).detach().numpy()
    real_part = y[:,0,:][0]
    imag_part = y[:,1,:][0]
    mag_part = (real_part**2+imag_part**2)**.5
    if output_folder is not None:
        pd.DataFrame({"real":real_part,"imag":imag_part}).to_csv(
        f"{output_folder}/outputs_{file_suffix}.csv")
    return real_part,imag_part,mag_part

def emulate_nn_batch(test_parameters
#,output_folder,file_suffix
):
    nn_columns_ordered = np.array(['length of patch', 'width of patch', 'height of patch',
       'height of substrate', 'height of solder resist layer',
       'radius of the probe', 'c_pad', 'c_antipad', 'c_probe',
       'dielectric constant of substrate',
       'dielectric constant of solder resist layer'])
    x = test_parameters[nn_columns_ordered]
    # x.to_csv(f"{output_folder}/inputs_{file_suffix}.csv")
    scaler = joblib.load("NNModel/scaler.gz")
    x_scaled = scaler.transform(x)
    model = NeuralNet()#.to(device="cpu")
    model.load_state_dict(torch.load("NNModel/trained_model.pt"))
    y = model(torch.tensor(x_scaled).float()).detach().numpy()
    real_part = y[:,0,:]
    imag_part = y[:,1,:]
    mag_part = (real_part**2+imag_part**2)**.5
    output_to_export = np.hstack([real_part,imag_part])
    output_to_export_cols = [f"real_{str(i).zfill(6)}" for i in range(real_part.shape[1])]
    output_to_export_cols.extend([f"imag_{str(i).zfill(6)}" for i in range(imag_part.shape[1])])
    # pd.DataFrame(output_to_export,columns=output_to_export_cols).to_csv(
    # f"{output_folder}/outputs_{file_suffix}.csv")
    return real_part,imag_part,mag_part





class OptimizationModel:
    def __init__(self,inputs,outputs) -> None:

        self.outputs = outputs
        self.inputs = inputs
        self.n_timesteps = outputs.shape[1]
        pass

    def fit_svd(self,n_components):
        self.n_components = n_components
        self.svd = TruncatedSVD(n_components=n_components,random_state=1)
        self.svd.fit(self.outputs)
        self.coordinates = self.svd.transform(self.outputs)
        self.coordinates_min = self.coordinates.min(0)
        self.coordinates_max = self.coordinates.max(0)

    def set_curve_parameters(self,curve_params_dict):
        self.curve_param_s = curve_params_dict["s"]
        self.curve_param_e = curve_params_dict["e"]
        self.curve_param_t = curve_params_dict["t"]
        self.curve_param_r = curve_params_dict["r"]

    def set_goal_coefficients(self,goal_coefs_dict):
        self.goal_coefs = goal_coefs_dict

    def create_model(self,similarity_config,sep,sim_mean):
        self.prob = pulp.LpProblem("Minimize_L1_Distance", pulp.LpMinimize)

        s = self.curve_param_s
        e = self.curve_param_e
        t = self.curve_param_t
        r = self.curve_param_r

        X = self.inputs.copy()
        Y = self.outputs.copy()
        Y_sample = Y.copy()
        if similarity_config["use_similarity"]:
            if similarity_config["use_all_data"] == False:
                np.random.shuffle(Y_sample)
                Y_sample = Y_sample[-similarity_config["sample_size"]:]

        W = self.svd.components_.copy()
        if "PCA" in str(type(self.svd)):
            U = self.svd.mean_.copy()*0
        else:
            U = np.zeros(Y.shape[1])

        prob = pulp.LpProblem("Minimize_L1_Distance", pulp.LpMinimize)
        A = [pulp.LpVariable(f'A_{i}', lowBound=0, upBound=1) for i in range(self.n_timesteps)]
        B = [pulp.LpVariable(f'B_{i}', lowBound=None, upBound=None) for i in range(self.n_components)]
        D = [pulp.LpVariable(f'D_{i}', lowBound=0, upBound=None) for i in range(self.n_timesteps)]
        if similarity_config["use_similarity"]:
            E = pulp.LpVariable.dicts("E_", ((i,k) for i in range(Y_sample.shape[0]) for k in range(self.n_timesteps)),lowBound=0,upBound=None)
        # H = [pulp.LpVariable(f'H_{i}', lowBound=0, upBound=None) for i in range(Y_sample.shape[0])]
        G1 = [pulp.LpVariable(f'G1_{i}', lowBound=None, upBound=None) for i in range(self.n_timesteps-1)]
        G2 = [pulp.LpVariable(f'G2_{i}', lowBound=None, upBound=None) for i in range(self.n_timesteps-3)]
        H = pulp.LpVariable(f'J', lowBound=0, upBound=None)
        self.dv_reconstructed = A
        self.dv_coordinates = B


        for k in range(Y.shape[1]):
            prob += A[k] == pulp.lpSum([B[m]*W[m][k]+U[k] for m in range(len(B))]), f"recon_{k}"

        for k in range(Y.shape[1]):
            if s <= k <= e:
                prob += A[k] - D[k]  <= t, f"threshold_{k}"
            else:
                prob += A[k] + D[k]  >= t, f"threshold_{k}"

            if k >= 1:
                prob += G1[k-1] >= (A[k]-A[k-1])
                prob += G1[k-1] >= -(A[k]-A[k-1])
                if k >= 3:
                    prob += G2[k-3] >= (A[k]-A[k-1])-(A[k-2]-A[k-3])
                    prob += G2[k-3] >= -((A[k]-A[k-1])-(A[k-2]-A[k-3]))
        if similarity_config["use_similarity"]:
            for i in range(Y_sample.shape[0]):
                for k in range(self.n_components):
                    prob += E[(i,k)] >= (B[k] - self.coordinates[i,k]), f"featuredist_abs1_{i}_{k}"
                    prob += E[(i,k)] >= (self.coordinates[i,k] - B[k]), f"featuredist_abs2_{i}_{k}"
                prob += H >= pulp.lpSum([E[(i,k2)] for k2 in range(self.n_components)])

        prob += (0
                + (((+ pulp.lpSum(A[s:e+1])/(e+1-s)+ (-(pulp.lpSum(A[:s])+pulp.lpSum(A[e+1:])))/(201-(e+1-s)))/2) if sep else (
                    (pulp.lpSum(A[s:e+1])-(pulp.lpSum(A[:s])+pulp.lpSum(A[e+1:])))/201
                ))
                + self.goal_coefs["c_similarity"]  * (((pulp.lpSum(E)/(Y_sample.shape[0]*self.n_components)) if sim_mean else (pulp.lpSum(H)/self.n_components)) 
                                                      if similarity_config["use_similarity"] else 0) # Similarity
                , f"obj")
        

        self.prob = prob

    def solve_model(self,output_folder,file_suffix):
        self.prob.solve()
        if self.prob.status != 1:
            raise Exception("LP couldn't be solved!")
        recon = self.get_reconstructed()
        pd.DataFrame(recon).to_csv(f"{output_folder}/recon_{file_suffix}.csv")
        
        coord = self.get_coordinates()
        pd.DataFrame(coord).to_csv(f"{output_folder}/coord_{file_suffix}.csv")
        
        del recon,coord


    def get_coordinates(self):
        return self.svd.transform([[e.varValue for e in self.dv_reconstructed]])[0]
        
    def get_reconstructed(self):
        return np.array([e.varValue for e in self.dv_reconstructed])
        

def calculate_perf(mag,s,e,t):
    return (mag[:,s:e+1] < t).mean(1)

def calculate_perf_mag(mag,s,e,t):
    return 1-(mag[:,s:e+1]).mean(1)

def calculate_perf_mag_relative(mag,s,e,t):
    # return (((1-mag[:,s:e+1])*(mag[:,s:e+1].mean(0))).mean(1))
    return (((1-mag[:,s:e+1])*(1-(mag[:,s:e+1] < t).mean(0))).mean(1))



def calculate_perf_full(mag,s,e,t):
    return ((mag[:,s:e+1] < t).mean(1)+
        ((mag[:,:s] >= t).sum(1)+(mag[:,e+1:] >= t).sum(1))/(mag.shape[1]-(e+1-s)))*.5

def calculate_perf_full_mask(mag,s,e,t):
    return 1-(((mag - np.array([1 if (i>=s) & (i<=e) else 0 for i in range(mag.shape[1])]).reshape(1,-1))**2).sum(1)**.5)/(mag.shape[1])



class InverseModel:
    def __init__(self) -> None:
        pass

    def fit_dt(self,X,Y,sampling_method,mags,s,e,t,output_folder=None,file_suffix=None):
        # X design, Y PCA
        self.mms = MinMaxScaler()
        self.mms.fit(X)
        X_scaled = self.mms.transform(X)
        if sampling_method["min_samples_leaf_rule"] == "max5ins-10perc":
            min_samples_leaf = int(max(5,len(X)*.1))
            self.inv_model = DecisionTreeRegressor(min_samples_leaf=min_samples_leaf)
        elif sampling_method["min_samples_leaf_rule"] == "max5ins-20perc":
            min_samples_leaf = int(max(5,len(X)*.2))
            self.inv_model = DecisionTreeRegressor(min_samples_leaf=min_samples_leaf)
        elif sampling_method["min_samples_leaf_rule"] == "5":
            min_samples_leaf = 5
            self.inv_model = DecisionTreeRegressor(min_samples_leaf=min_samples_leaf)
        self.inv_model.fit(Y,X_scaled)
        if sampling_method["leaf_selection_perf"] == "perf":
            self.perfs = calculate_perf(mags,s,e,t)
        if sampling_method["leaf_selection_perf"] == "perf_full":
            self.perfs = calculate_perf_full(mags,s,e,t)
        if sampling_method["leaf_selection_perf"] == "perf_ful_mask":
            self.perfs = calculate_perf_full_mask(mags,s,e,t)
        
        if output_folder:
            pd.DataFrame(self.inv_model.apply(Y)).to_csv(f"{output_folder}/inputlabel_{file_suffix}.csv")
        

    def select_leaf_by_UCB(self,X,Y,sampling_method,sigma_coef = 1,output_folder = None,file_suffix=None):
        leaves_of_data = self.inv_model.apply(Y)
        leaves_perf = pd.DataFrame({"leaf":leaves_of_data,"perf":self.perfs}) 
        leaves_perf = leaves_perf.groupby(["leaf"])["perf"].describe()[["mean","std"]]
        leaves_perf["UCB"] = leaves_perf["mean"]+sigma_coef*leaves_perf["std"]
        leaf_selected = leaves_perf.reset_index().sort_values("UCB",ascending=False)["leaf"].iloc[0]
        if output_folder:
            pd.DataFrame({"leaf_selected":[leaf_selected]}).to_csv(f"{output_folder}/leafselected_{file_suffix}.csv")
        return leaf_selected

    def select_in_leaf(self,X,Y,sampling_method,leaf_selected,output_folder=None,file_suffix=None):        

        sample_per_leaf =sampling_method["sample_per_leaf"] 
        leaves_of_data = self.inv_model.apply(Y)
        idx_of_selected_obs = leaves_of_data == leaf_selected
        X_leaf = X[idx_of_selected_obs]
        X_leaf_min = X_leaf.min(0)
        X_leaf_max = X_leaf.max(0)


        
        if sampling_method["maximize_minl2dist"]:
            X_scaled_bounds = (X-INPUT_MIN)/(INPUT_MAX-INPUT_MIN)
            # X_scaled_corners = np.array([[int(i) for i in bin(j)[2:].zfill(11)] for j in range(int(2**11))])
            # X_scaled_bounds_w_corners = np.concatenate([X_scaled_bounds,X_scaled_corners])

            X_leaf_min_scaled_bounds = (X_leaf_min-INPUT_MIN)/(INPUT_MAX-INPUT_MIN)
            X_leaf_max_scaled_bounds = (X_leaf_max-INPUT_MIN)/(INPUT_MAX-INPUT_MIN)

            n_geom_feats = X.shape[1]
            def solve_dist_prob():
                linear_constraint_lb = np.append(-100000,X_leaf_min_scaled_bounds)
                linear_constraint_ub = np.append(100000,X_leaf_max_scaled_bounds)
                linear_constraint = LinearConstraint(np.eye(1+n_geom_feats),linear_constraint_lb,linear_constraint_ub)

                def objective_func(x):
                    return -x[0]
                def objective_jacobian(x):
                    return np.array([-1 if i == 0 else 0 for i in range(n_geom_feats+1)]).astype(float)
                def objective_hessian(x):
                    return np.zeros(n_geom_feats+1).astype(float)


                def nonlinear_constraint_func(x):
                    return [x[0]-sum([(x[j+1]-X_scaled_bounds[i,j])**2 for j in range(n_geom_feats)])/2 for i in range(X_scaled_bounds.shape[0])]
                def nonlinear_constraint_jacobian(x):
                    return [[1 if j == 0 else -(x[j]-X_scaled_bounds[i,j-1]) for j in range(n_geom_feats+1)] for i in range(X_scaled_bounds.shape[0])]
                def nonlinear_constraint_hessian(x,v):
                    h = -np.eye(n_geom_feats+1)
                    h[0][0] = 0
                    return sum(v[i]*h for i in range(X_scaled_bounds.shape[0]))
                nonlinear_constraint = NonlinearConstraint(nonlinear_constraint_func, -np.inf, 0, jac=nonlinear_constraint_jacobian, hess=nonlinear_constraint_hessian)
                x0 = np.random.random(n_geom_feats+1)

                prob_maxofmindist = minimize(objective_func, x0, method='trust-constr', jac=objective_jacobian, hess=objective_hessian,
                            constraints=[linear_constraint, nonlinear_constraint],
                            options={'verbose': 0})
                return prob_maxofmindist.x
            dist_prob_solutions = np.array([solve_dist_prob() for i in range(100)])
            dist_prob_solutions_best = dist_prob_solutions[np.argmax(dist_prob_solutions[:,0])][1:]
            dist_prob_solutions_best = INPUT_MIN+dist_prob_solutions_best*INPUT_RANGE
            return dist_prob_solutions_best

        response_all_leaf = None
        while True:
            if sampling_method["type"] == "uniform":
                response_added = X_leaf_min+(X_leaf_max-X_leaf_min)*np.random.rand(sample_per_leaf,X_leaf.shape[1])
            # response_invtr = self.mms.inverse_transform(response)
            # response_added = self.mms.inverse_transform(response_added)
            is_bounded = ((response_added>=INPUT_MIN).all(1) & (response_added<=INPUT_MAX).all(1))
            response_added  = response_added[is_bounded]
            if len(response_added > 0):
                if response_all_leaf is not None:
                    response_all_leaf = np.vstack([response_all_leaf,response_added])
                else:
                    response_all_leaf = response_added.copy()
            if  len(response_all_leaf) >= sample_per_leaf:
                response_all_leaf = response_all_leaf[:sample_per_leaf]
                break
            
        if sampling_method["acquisition"] == "MaxOfMinInputDist":
            X_min,X_max = X.min(0),X.max(0)
            X_scaled = (X-X_min)/(X_max-X_min)

            response_all_scaled = (response_all_leaf-X_min)/(X_max-X_min)
            response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
            response_all_dists_to_X_min_scaled = response_all_dists_to_X_min/response_all_dists_to_X_min.max()
            
            acquisition = response_all_dists_to_X_min_scaled.copy()
            
            response = response_all_leaf[acquisition.argmax()]#.reshape(1,-1)
            return response

    def sample_dt(self,X,Y,Y_target,sampling_method,is_bounded=True):
        sample_per_leaf =sampling_method["sample_per_leaf"] 
        leaf_selection = sampling_method["leaf_selection"]
        X_scaled = self.mms.transform(X)
        leaf_of_test_obs = self.inv_model.apply(Y_target)
        leaves_of_training_data = self.inv_model.apply(Y)
        train_data_Y_in_test_leaf = X_scaled[leaves_of_training_data == leaf_of_test_obs]
        response_mean = train_data_Y_in_test_leaf.mean(0)
        response_std = train_data_Y_in_test_leaf.std(0)
        if sampling_method["type"] == "kde":
            kde = KernelDensity(bandwidth=sampling_method["bw"])
            kde.fit(train_data_Y_in_test_leaf)
        # response_cov = np.cov(train_data_Y_in_test_leaf.T)
        
        if sample_per_leaf is None:
            while True:
                # response = np.random.multivariate_normal(response_mean,response_var).reshape(1,-1)
                
                if sampling_method["type"] == "kde":
                    response = kde.sample().reshape(1,-1)
                elif sampling_method["type"] == "ind_gaussian":
                    response = np.random.normal(response_mean,response_std).reshape(1,-1) # Çoklu sample'la dene
                elif sampling_method["type"] == "uniform":
                    response = train_data_Y_in_test_leaf.min(0)+(train_data_Y_in_test_leaf.max(0)-train_data_Y_in_test_leaf.min(0))*np.random.rand(train_data_Y_in_test_leaf.shape[1])
                    response = response.reshape(1,-1)
                response_invtr = self.mms.inverse_transform(response)
                if is_bounded:
                    if ((response_invtr>=INPUT_MIN).all() &
                    (response_invtr<=INPUT_MAX).all()): 
                        break
                else:
                    if (response_invtr >= 0).all():
                        break
            return response_invtr
        else:
            response_all = []
            response_all_leaf = None
            while True:
                if sampling_method["type"] == "ind_gaussian":
                    response_added = np.random.multivariate_normal(response_mean,np.eye(len(response_std))*response_std**2,size=100)
                elif sampling_method["type"] == "uniform":
                    response_added = train_data_Y_in_test_leaf.min(0)+(train_data_Y_in_test_leaf.max(0)-train_data_Y_in_test_leaf.min(0))*np.random.rand(sample_per_leaf,train_data_Y_in_test_leaf.shape[1])
                # response_invtr = self.mms.inverse_transform(response)
                response_added = self.mms.inverse_transform(response_added)
                is_bounded = ((response_added>=INPUT_MIN).all(1) & (response_added<=INPUT_MAX).all(1))
                response_added  = response_added[is_bounded]
                if len(response_added > 0):
                    if response_all_leaf is not None:
                        response_all_leaf = np.vstack([response_all_leaf,response_added])
                    else:
                        response_all_leaf = response_added.copy()
                if  len(response_all_leaf) >= sample_per_leaf:
                    response_all_leaf = response_all_leaf[:sample_per_leaf]
                    response_all.append(response_all_leaf)
                    break
            response_all = response_all_leaf.copy()

            if sampling_method["acquisition"] == "TargetPCA&MinInputDist":
                Y_min,Y_max = Y.min(0),Y.max(0)
                Y_scaled = (Y-Y_min)/(Y_max-Y_min)

                response_all_scaled = (response_all-Y_min)/(Y_max-Y_min)
                response_all_dists_to_Y_min = euclidean_distances(response_all_scaled,Y_scaled).min(1)
                response_all_dists_to_Y_min_scaled = response_all_dists_to_Y_min/response_all_dists_to_Y_min.max()
                
                response_target_dists = ((self.inv_model.predict(response_all)-Y_target.reshape(1,-1))**2).sum(1)**.5
                response_target_dists_scaled = response_target_dists/response_target_dists.max()

                acquisition = 0.5*response_target_dists_scaled+0.5*(1-response_all_dists_to_Y_min_scaled)
                
                response = response_all[acquisition.argmax()].reshape(1,-1)
                return response
            elif sampling_method["acquisition"] == "MaxOfMinInputDist":
                Y_min,Y_max = Y.min(0),Y.max(0)
                Y_scaled = (Y-Y_min)/(Y_max-Y_min)

                response_all_scaled = (response_all-Y_min)/(Y_max-Y_min)
                response_all_dists_to_Y_min = euclidean_distances(response_all_scaled,Y_scaled).min(1)
                response_all_dists_to_Y_min_scaled = response_all_dists_to_Y_min/response_all_dists_to_Y_min.max()
                
                acquisition = response_all_dists_to_Y_min_scaled.copy()
                
                response = response_all[acquisition.argmax()].reshape(1,-1)
                return response

class LinearTreeForward:
    def __init__(self) -> None:
        pass

    def get_geometry(self,X,Y,mags,output_folder,file_suffix):
        X_scaled = (X-X.mean(0))/X.std(0)
        reg = LinearTreeRegressor(base_estimator=MultiTaskLassoCV(n_alphas=5),min_samples_leaf=5)
        reg.fit(X_scaled, Y)
        X_sample = INPUT_MIN+np.random.random([10000,len(INPUT_RANGE)])*INPUT_RANGE
        X_sample_scaled = (X_sample-X.mean(0))/X.std(0)
        Y_sample = reg.predict(X_sample_scaled)
        sample_selected_idx = Y_sample[:,100:151].mean(1).argmin()
        return X_sample[sample_selected_idx]

class ForwardModel:
    def __init__(self,bo_model=None) -> None:
        self.bo_model = bo_model
        pass

    def fit_dt_without_scaling(self,X,Y,
    mags,s,e,t,sampling_method,output_folder=None,file_suffix=None,
    ):
        n_nodes = None
        if (sampling_method["n_nodes_max"] is not None):
            n_nodes = sampling_method["n_nodes_max"]
        self.fw_model = DecisionTreeRegressor(min_samples_leaf=5,
                                max_leaf_nodes = n_nodes,
            )
        self.fw_model.fit(X,Y)
        self.perfs = calculate_perf(mags,s,e,t)
        
        if "leaf_selection_perf" in sampling_method.keys():
            if sampling_method["leaf_selection_perf"] == "perf_mag":
                self.perfs = calculate_perf_mag(mags,s,e,t)
            if sampling_method["leaf_selection_perf"] == "perf_mag_relative":
                self.perfs = calculate_perf_mag_relative(mags,s,e,t)

        if output_folder:
            pd.DataFrame(self.fw_model.apply(X)).to_csv(f"{output_folder}/inputlabel_{file_suffix}.csv")

    def fit_dt(self,X,Y,
    mags,s,e,t,output_folder=None,file_suffix=None):

        
        self.mms = MinMaxScaler()
        self.mms.fit(Y)
        Y_scaled = self.mms.transform(Y)
        self.fw_model = DecisionTreeRegressor(min_samples_leaf=5,
        )
        self.fw_model.fit(X,Y_scaled)

    def reg_on_nodes(self,X,Y,
    mags,s,e,t,sampling_method,output_folder=None,file_suffix=None,i_iter=None):
        nodes = self.fw_model.apply(X).astype(int)
        sample_X_all = []
        sample_Y_all = []
        sample_node_all = []

        # svd = TruncatedSVD(15,random_state=1)

        for node in sorted(list(set(nodes))):
            node_idx = nodes == node
            X_node = X[node_idx]
            X_node_min,X_node_max = X_node.min(0),X_node.max(0)
            mags_node = mags[node_idx]
            # Y_node = self.svd.transform(mags_node)
            # lr = MultiTaskLassoCV()
            lr = LinearRegression()
            lr.fit(X_node,mags_node)
            # .to_csv(f"{output_folder}/inputselectedlabel_{file_suffix}.csv")
            joblib.dump(lr, f"{output_folder}/lr_node{str(node).zfill(3)}_{file_suffix}.pkl") 

            margin = .001*(i_iter+1)
            sample_X = X_node_min+(X_node_max-X_node_min)*(-margin+(1+2*margin)*np.random.random([10000,11]))
            sample_X = sample_X[((sample_X >= INPUT_MIN) & (sample_X <= INPUT_MAX)).all(1)]
            
            sample_Y_pred = lr.predict(sample_X)
            # sample_Y_pred = self.svd.inverse_transform(sample_Y_pred)
            sample_Y_pred_clamped = np.minimum(sample_Y_pred,1)
            sample_Y_pred_clamped = np.maximum(sample_Y_pred_clamped,0)

            sample_X_all.append(sample_X)
            sample_Y_all.append(sample_Y_pred_clamped)
            sample_node_all.append([node]*len(sample_X))
        
        sample_X_all = np.concatenate(sample_X_all)
        sample_Y_all = np.concatenate(sample_Y_all)
        sample_node_all = np.concatenate(sample_node_all)
        selected_idx = (sample_Y_all[:,s:e+1]<t).mean(1).argmax()
        selected_X = sample_X_all[selected_idx]
        # sample_perfs = (sample_Y_all[:,s:e+1]<t).mean(1)
        # # if sample_perfs.sum() == 0:
        # #     return self.select_outermost_from_all_edges(X,Y,
        # #                 mags,s,e,t,sampling_method,output_folder,file_suffix)
        # if 1 in sample_perfs:
        #     best_indices = np.where(sample_perfs == 1)[0]
        #     selected_idx = np.random.choice(best_indices)
        # else:
        #     selected_idx = np.argmax(sample_perfs)
        leaf_selected = sample_node_all[selected_idx]
        pd.DataFrame({"leaf_selected":[leaf_selected]}).to_csv(f"{output_folder}/inputselectedlabel_{file_suffix}.csv")
        return sample_X_all[selected_idx]

    def select_outermost_from_all_edges(self,X,Y,
    mags,s,e,t,sampling_method,output_folder=None,file_suffix=None,):
        leaf_selected = "all"
        pd.DataFrame({"leaf_selected":[leaf_selected]}).to_csv(f"{output_folder}/inputselectedlabel_{file_suffix}.csv")
        nodes = self.fw_model.apply(X).astype(int)
        # X_nodes_df = pd.DataFrame(X)
        # X_nodes_df["node"] = nodes
        # X_nodes_min = X_nodes_df.groupby("node").min().values
        # X_nodes_max = X_nodes_df.groupby("node").max().values
        X_min,X_max = X.min(0),X.max(0)

        sample_X = X_min+(X_max-X_min)*(np.random.random([1000000,11]))
        idx_samples_within_nodes = []
        for node in sorted(list(set(nodes))):
            node_idx = nodes == node
            X_node = X[node_idx]
            X_node_min,X_node_max = X_node.min(0),X_node.max(0)

            idx_samples_within_nodes.append(((sample_X > X_node_min) & (sample_X < X_node_max)).all(1))
        idx_samples_within_nodes = (np.vstack(idx_samples_within_nodes)*1).max(0)
        if (1-idx_samples_within_nodes).sum() != 0:
            sample_X=sample_X[idx_samples_within_nodes==0]

        idx = euclidean_distances(sample_X,X).min(1).argmax()
        return sample_X[idx]

    def select_increasing_search_space(self,X,Y,
    mags,s,e,t,sampling_method,output_folder=None,file_suffix=None,):
        leaf_selected = "all"
        pd.DataFrame({"leaf_selected":[leaf_selected]}).to_csv(f"{output_folder}/inputselectedlabel_{file_suffix}.csv")
        sample_X = INPUT_MIN+INPUT_RANGE*np.random.random([1000000,11])
        nodes = self.fw_model.apply(X).astype(int)
        nodes_params_min = np.zeros([max(nodes)+1,11])
        nodes_params_max = np.zeros([max(nodes)+1,11])
        for node in sorted(list(set(nodes))):
            node_idx = nodes == node
            nodes_params_min[node] = X[node_idx].min(0)
            nodes_params_max[node] = X[node_idx].max(0)
        sample_nodes = self.fw_model.apply(sample_X).astype(int)
        old_frontiers = nodes_params_max[sample_nodes]-nodes_params_min[sample_nodes]
        new_frontiers = np.maximum(nodes_params_max[sample_nodes],sample_X)-np.minimum(nodes_params_min[sample_nodes],sample_X)
        vol_changes = (new_frontiers/INPUT_RANGE).prod(1)-(old_frontiers/INPUT_RANGE).prod(1)
        selected_idx = vol_changes.argmax()
        selected_X = sample_X[selected_idx]
        return selected_X

    def fit_predict_mags_lgbm(self,X,Y,
        mags,s,e,t,output_folder=None,file_suffix=None):

        lgb_model = lightgbm.LGBMRegressor(n_jobs=2,max_depth=5,min_samples_leaf=10)
        model = MultiOutputRegressor(lgb_model)
        model.fit(X,Y)

        X_sample = INPUT_MIN+np.random.random([10000,len(INPUT_RANGE)])*INPUT_RANGE
        Y_sample = model.predict(X_sample)

        selected_idx = Y_sample[:,s:e+1].mean(1).argmin()
        return X_sample[selected_idx]



    def select_leaf_by_UCB(self,X,Y,sampling_method,current_iter=None):
        sigma_coef = sampling_method["sigma_coef"]
        leaves_of_data = self.fw_model.apply(X)
        n_iter_for_var_only = sampling_method["var_only_leaf_in_each"]
        leaves_perf = pd.DataFrame({"leaf":leaves_of_data,"perf":self.perfs})
        # leaves_perf["reverse_order"] = leaves_perf.groupby("leaf").cumcount(ascending=False)
        # leaves_perf = leaves_perf[leaves_perf["reverse_order"] < 5]
        leaves_perf = leaves_perf.groupby(["leaf"])["perf"].describe()[["mean","std"]]
        leaves_perf["UCB"] = leaves_perf["mean"]+sigma_coef*leaves_perf["std"]
        if (leaves_perf["mean"].max() <= 0.00001) | (sampling_method["searchInFull"] == True):
            leaf_selected = "all"
        else:    
            if  (n_iter_for_var_only is None):
                leaf_selected = leaves_perf.reset_index().sort_values("UCB",ascending=False)["leaf"].iloc[0]
            elif ((current_iter%n_iter_for_var_only) != (n_iter_for_var_only-1)):
                leaf_selected = leaves_perf.reset_index().sort_values("UCB",ascending=False)["leaf"].iloc[0]
            else:
                leaf_selected = leaves_perf.reset_index().sort_values("std",ascending=False)["leaf"].iloc[0]


        return leaf_selected

    def select_in_leaf(self,X,Y,Y_mags,sampling_method,leaf_selected,output_folder=None,file_suffix=None):
        # sample_per_leaf = int(sampling_method["sample_per_leaf"]/(int(file_suffix)+1))
        sample_per_leaf = sampling_method["sample_per_leaf"]
        
        if output_folder:
            pd.DataFrame({"leaf_selected":[leaf_selected]}).to_csv(f"{output_folder}/inputselectedlabel_{file_suffix}.csv")
        leaves_of_data = self.fw_model.apply(X)
        if leaf_selected == "all":
            idx_of_selected_obs = np.array([True]*len(leaves_of_data))
        else:
            idx_of_selected_obs = leaves_of_data == leaf_selected
        X_leaf = X[idx_of_selected_obs]
        

            
        if sampling_method["sample_in_boundaries"]:
            dec_path = self.fw_model.tree_.decision_path(X_leaf.astype(np.float32)[:1]).A[0] == 1
            dec_path_nodes = np.where(dec_path)[0]
            dec_path_features = self.fw_model.tree_.feature[dec_path]
            dec_path_thresholds = self.fw_model.tree_.threshold[dec_path]
            dec_path_left = self.fw_model.tree_.children_left[dec_path]
            dec_path_right = self.fw_model.tree_.children_right[dec_path]

            dec_rules = []
            dec_rules_to_print = []
            for i in range(len(dec_path_nodes)-1):
                if dec_path_nodes[i+1] == dec_path_left[i]:
                    dec_rules.append([dec_path_features[i],"<=",dec_path_thresholds[i]])
                    dec_rules_to_print.append([dec_path_features[i],-1,dec_path_thresholds[i]])
                    # print(f"fetaure {dec_path_features[i]} <= {dec_path_thresholds[i]}")
                else:
                    dec_rules.append([dec_path_features[i],">",dec_path_thresholds[i]])
                    dec_rules_to_print.append([dec_path_features[i],1,dec_path_thresholds[i]])
                    # print(f"fetaure {dec_path_features[i]} > {dec_path_thresholds[i]}")
            dec_rules_to_print = pd.DataFrame(dec_rules_to_print)
            if dec_rules_to_print.shape[0] != 0:
                dec_rules_to_print.columns = ["feat","dir","thres"]
            dec_rules_to_print.to_csv(f"{output_folder}/leafselectedbounds_{file_suffix}.csv")

            # X_leaf_min = INPUT_MIN.copy()
            # X_leaf_max = INPUT_MAX.copy()
            X_leaf_min = X_leaf.min(0)
            X_leaf_max = X_leaf.max(0)
            for dec_rule in dec_rules:
                dec_feat,dec_dir,dec_thres = dec_rule
                if dec_dir == "<=":
                    X_leaf_max[dec_feat] = max(X_leaf_max[dec_feat],dec_thres)
                elif dec_dir == ">":
                    X_leaf_min[dec_feat] = min(X_leaf_min[dec_feat],dec_thres)
                else:
                    None * 1
            X_leaf_min = np.maximum(X_leaf_min,INPUT_MIN)
            X_leaf_max = np.minimum(X_leaf_max,INPUT_MAX)
            
        else:
            X_leaf_min = X_leaf.min(0)
            X_leaf_max = X_leaf.max(0)

        if sampling_method["select_by_perf_reg"]:
            n_poly = np.random.choice(np.arange(2,len(X_leaf)+1))
            perf2 = 1-Y_mags[idx_of_selected_obs,100:151].mean(1)
            design_data = X_leaf.copy()
            design_data_mean = design_data.mean(0)
            design_data_std = design_data.std(0)+.0001
            design_data_scaled = (design_data-design_data_mean)/design_data_std
            design_pca = PCA(1)
            design_pca_coefs = design_pca.fit_transform(design_data_scaled)
            lr = LinearRegression()
            lr.fit(PolynomialFeatures(n_poly).fit_transform(design_pca_coefs),perf2)

            design_pca_coefs_min = design_pca_coefs.min()
            design_pca_coefs_max = design_pca_coefs.max()
            design_pca_coefs_range = design_pca_coefs_max-design_pca_coefs_min
            design_pca_coefs_min_limit = design_pca_coefs_min+design_pca_coefs_range*.1
            design_pca_coefs_max_limit = design_pca_coefs_max-design_pca_coefs_range*.1
            reg_sample_x = np.linspace(design_pca_coefs_min_limit,design_pca_coefs_max_limit,10000).reshape(-1,1)
            reg_sample_x_poly = PolynomialFeatures(n_poly).fit_transform(reg_sample_x)
            reg_sample_y = lr.predict(reg_sample_x_poly)

            response = design_pca.inverse_transform(reg_sample_x[reg_sample_y.argmax()])*design_data_std+design_data_mean
            response = response+np.random.randn(len(INPUT_RANGE))*INPUT_RANGE*.1
            response = np.minimum(response,X_leaf_max)
            response = np.maximum(response,X_leaf_min)
            return response

        if "searchBayesian" in sampling_method.keys(): 
            if sampling_method["searchInFull"] == True:
                X_leaf_min = INPUT_MIN.copy()
                X_leaf_max = INPUT_MAX.copy()
            # self.bo_model.add_initials_manually(idx_of_selected_obs)
            self.bo_model.add_initials_manually(np.array([True]*len(leaves_of_data)))
            self.bo_model.set_limits(X_leaf_min,X_leaf_max)
            self.bo_model.run_study()
            response = self.bo_model.get_parameters()
            if (response<X_leaf_min).sum() > 0:
                raise ValueError("Out of range")
            elif (response>X_leaf_max).sum() > 0:
                raise ValueError("Out of range")
            return response

        if sampling_method["maximize_minl2dist"]:
            X_scaled_bounds = (X-INPUT_MIN)/(INPUT_MAX-INPUT_MIN)
            # X_scaled_corners = np.array([[int(i) for i in bin(j)[2:].zfill(11)] for j in range(int(2**11))])
            # X_scaled_bounds_w_corners = np.concatenate([X_scaled_bounds,X_scaled_corners])

            X_leaf_min_scaled_bounds = (X_leaf_min-INPUT_MIN)/(INPUT_MAX-INPUT_MIN)
            X_leaf_max_scaled_bounds = (X_leaf_max-INPUT_MIN)/(INPUT_MAX-INPUT_MIN)

            n_geom_feats = X.shape[1]
            def solve_dist_prob():
                linear_constraint_lb = np.append(-100000,X_leaf_min_scaled_bounds)
                linear_constraint_ub = np.append(100000,X_leaf_max_scaled_bounds)
                linear_constraint = LinearConstraint(np.eye(1+n_geom_feats),linear_constraint_lb,linear_constraint_ub)

                def objective_func(x):
                    return -x[0]
                def objective_jacobian(x):
                    return np.array([-1 if i == 0 else 0 for i in range(n_geom_feats+1)]).astype(float)
                def objective_hessian(x):
                    return np.zeros(n_geom_feats+1).astype(float)


                def nonlinear_constraint_func(x):
                    return [x[0]-sum([(x[j+1]-X_scaled_bounds[i,j])**2 for j in range(n_geom_feats)])/2 for i in range(X_scaled_bounds.shape[0])]
                def nonlinear_constraint_jacobian(x):
                    return [[1 if j == 0 else -(x[j]-X_scaled_bounds[i,j-1]) for j in range(n_geom_feats+1)] for i in range(X_scaled_bounds.shape[0])]
                def nonlinear_constraint_hessian(x,v):
                    h = -np.eye(n_geom_feats+1)
                    h[0][0] = 0
                    return sum(v[i]*h for i in range(X_scaled_bounds.shape[0]))
                nonlinear_constraint = NonlinearConstraint(nonlinear_constraint_func, -np.inf, 0, jac=nonlinear_constraint_jacobian, hess=nonlinear_constraint_hessian)
                x0 = np.random.random(n_geom_feats+1)

                prob_maxofmindist = minimize(objective_func, x0, method='trust-constr', jac=objective_jacobian, hess=objective_hessian,
                            constraints=[linear_constraint, nonlinear_constraint],
                            options={'verbose': 0})
                return prob_maxofmindist.x
            dist_prob_solutions = np.array([solve_dist_prob() for i in range(100)])
            dist_prob_solutions_best = dist_prob_solutions[np.argmax(dist_prob_solutions[:,0])][1:]
            dist_prob_solutions_best = INPUT_MIN+dist_prob_solutions_best*INPUT_RANGE
            return dist_prob_solutions_best

        response_all_leaf = None
        while True:
            if sampling_method["type"] == "uniform":
                response_added = X_leaf_min+(X_leaf_max-X_leaf_min)*np.random.rand(sample_per_leaf,X_leaf.shape[1])
            # response_invtr = self.mms.inverse_transform(response)
            # response_added = self.mms.inverse_transform(response_added)
            is_bounded = ((response_added>=INPUT_MIN).all(1) & (response_added<=INPUT_MAX).all(1))
            response_added  = response_added[is_bounded]
            if len(response_added > 0):
                if response_all_leaf is not None:
                    response_all_leaf = np.vstack([response_all_leaf,response_added])
                else:
                    response_all_leaf = response_added.copy()
            if  len(response_all_leaf) >= sample_per_leaf:
                response_all_leaf = response_all_leaf[:sample_per_leaf]
                break
        

            
        if sampling_method["acquisition"] == "MaxOfMinInputDist":
            X_min,X_max = X.min(0),X.max(0)
            X_scaled = (X-X_min)/(X_max-X_min)

            response_all_scaled = (response_all_leaf-X_min)/(X_max-X_min)
            response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
            response_all_dists_to_X_min_scaled = response_all_dists_to_X_min/response_all_dists_to_X_min.max()
            
            acquisition = response_all_dists_to_X_min_scaled.copy()
            
            response = response_all_leaf[acquisition.argmax()]#.reshape(1,-1)
            # response = np.median(X_leaf,axis=0) 
            # for rule_feat, rule_dir, rule_val in dec_rules:
            #     response[rule_feat] = rule_val
            return response
            
        if sampling_method["acquisition"] == "MaxMinInput&PairSlopeZero":
            X_min,X_max = X.min(0),X.max(0)
            X_scaled = (X-X_min)/(X_max-X_min)

            response_all_scaled = (response_all_leaf-X_min)/(X_max-X_min)
            response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
            response_all_dists_to_X_min_scaled = (response_all_dists_to_X_min-response_all_dists_to_X_min.min())/(response_all_dists_to_X_min.max()-response_all_dists_to_X_min.min())
            
            Y_res_mean = Y_mags[:,100:151].mean(1)

            res_mean_dist_coefs = Y_res_mean.reshape(-1,1)/(Y_res_mean.reshape(-1,1)-Y_res_mean.reshape(1,-1))
            X_for_pair_diff = X.reshape(X.shape[0],1,X.shape[1])
            X_pair_diffs = (X_for_pair_diff-X_for_pair_diff.transpose(1,0,2))
            inputs_with_zero_est = X_for_pair_diff-X_pair_diffs*res_mean_dist_coefs.reshape(res_mean_dist_coefs.shape[0],res_mean_dist_coefs.shape[1],1)
            inputs_with_zero_est = pd.DataFrame(inputs_with_zero_est[np.triu_indices(inputs_with_zero_est.shape[0])]).dropna().values

            zero_est_dists_min = euclidean_distances(response_all_leaf,inputs_with_zero_est).min(1)
            zero_est_dists_min_scaled = (zero_est_dists_min-zero_est_dists_min.min())/(zero_est_dists_min.max()-zero_est_dists_min.min())
            zero_est_sim_scaled = 1-zero_est_dists_min_scaled
            acquisition = response_all_dists_to_X_min_scaled+zero_est_sim_scaled
            
            response = response_all_leaf[acquisition.argmax()]#.reshape(1,-1)
            return response
            
        if sampling_method["acquisition"] == "MaxMinInput&PairSlopeZeroPerf":
            X_min,X_max = X.min(0),X.max(0)
            X_scaled = (X-X_min)/(X_max-X_min)

            response_all_scaled = (response_all_leaf-X_min)/(X_max-X_min)
            response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
            response_all_dists_to_X_min_scaled = (response_all_dists_to_X_min-response_all_dists_to_X_min.min())/(response_all_dists_to_X_min.max()-response_all_dists_to_X_min.min())
            
            Y_res_mean = 1-(Y_mags[:,100:151]<.3).mean(1)
            Y_res_mean = Y_res_mean + np.random.random(Y_res_mean.shape[0])*.01

            res_mean_dist_coefs = Y_res_mean.reshape(-1,1)/(Y_res_mean.reshape(-1,1)-Y_res_mean.reshape(1,-1))
            X_for_pair_diff = X.reshape(X.shape[0],1,X.shape[1])
            X_pair_diffs = (X_for_pair_diff-X_for_pair_diff.transpose(1,0,2))
            inputs_with_zero_est = X_for_pair_diff-X_pair_diffs*res_mean_dist_coefs.reshape(res_mean_dist_coefs.shape[0],res_mean_dist_coefs.shape[1],1)
            inputs_with_zero_est = pd.DataFrame(inputs_with_zero_est[np.triu_indices(inputs_with_zero_est.shape[0])]).dropna().values

            zero_est_dists_min = euclidean_distances(response_all_leaf,inputs_with_zero_est).min(1)
            zero_est_dists_min_scaled = (zero_est_dists_min-zero_est_dists_min.min())/(zero_est_dists_min.max()-zero_est_dists_min.min())
            zero_est_sim_scaled = 1-zero_est_dists_min_scaled
            acquisition = response_all_dists_to_X_min_scaled+zero_est_sim_scaled
            
            response = response_all_leaf[acquisition.argmax()]#.reshape(1,-1)
            return response
            
        if sampling_method["acquisition"] == "PairSlopeZeroPerf":
            X_min,X_max = X.min(0),X.max(0)
            X_scaled = (X-X_min)/(X_max-X_min)

            response_all_scaled = (response_all_leaf-X_min)/(X_max-X_min)
            response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
            response_all_dists_to_X_min_scaled = (response_all_dists_to_X_min-response_all_dists_to_X_min.min())/(response_all_dists_to_X_min.max()-response_all_dists_to_X_min.min())
            
            Y_res_mean = 1-(Y_mags[:,100:151]<.3).mean(1)
            Y_res_mean = Y_res_mean + np.random.random(Y_res_mean.shape[0])*.01

            res_mean_dist_coefs = Y_res_mean.reshape(-1,1)/(Y_res_mean.reshape(-1,1)-Y_res_mean.reshape(1,-1))
            X_for_pair_diff = X.reshape(X.shape[0],1,X.shape[1])
            X_pair_diffs = (X_for_pair_diff-X_for_pair_diff.transpose(1,0,2))
            inputs_with_zero_est = X_for_pair_diff-X_pair_diffs*res_mean_dist_coefs.reshape(res_mean_dist_coefs.shape[0],res_mean_dist_coefs.shape[1],1)
            inputs_with_zero_est = pd.DataFrame(inputs_with_zero_est[np.triu_indices(inputs_with_zero_est.shape[0])]).dropna().values

            zero_est_dists_min = euclidean_distances(response_all_leaf,inputs_with_zero_est).min(1)
            zero_est_dists_min_scaled = (zero_est_dists_min-zero_est_dists_min.min())/(zero_est_dists_min.max()-zero_est_dists_min.min())
            zero_est_sim_scaled = 1-zero_est_dists_min_scaled
            acquisition = zero_est_sim_scaled
            
            response = response_all_leaf[acquisition.argmax()]#.reshape(1,-1)
            return response

    def sample_dt(self,X,Y,Y_target,sampling_method,is_bounded=True):
        sample_per_leaf =sampling_method["sample_per_leaf"] 
        leaf_selection = sampling_method["leaf_selection"]
        Y_scaled = self.mms.transform(Y)
        Y_target_scaled = self.mms.transform(Y_target)
        leaves_of_training_data = self.fw_model.apply(X)
        leaves = list(set(leaves_of_training_data))
        leaf_scores = []
        leaf_logpdf_list = []
        leaf_l2_median_dists = []
        leaf_kde_scores = []
        if sample_per_leaf is None:
            for leaf in leaves:
                leaf_data_Y = Y_scaled[leaves_of_training_data == leaf]
                leaf_mean,leaf_var = leaf_data_Y.mean(0),leaf_data_Y.var(0)
                prob_dist = multivariate_normal(leaf_mean,leaf_var)
                # leaf_score = prob_dist.pdf(Y_target_scaled,leaf_mean)
                leaf_score = 1/(prob_dist.logpdf(leaf_mean)-prob_dist.logpdf(Y_target_scaled))
                leaf_scores.append(leaf_score)
                leaf_logpdf = prob_dist.logpdf(Y_target_scaled)
                leaf_logpdf_list.append(leaf_logpdf)
                if leaf_selection == "kde_max":
                    leaf_kde = KernelDensity(bandwidth=sampling_method["dist_bw"])
                    leaf_kde.fit(leaf_data_Y)
                    leaf_kde_score = np.exp(leaf_kde.score_samples(Y_target_scaled))[0]
                    leaf_kde_scores.append(leaf_kde_score)
                leaf_l2_dist_to_median = ((leaf_data_Y - Y_target_scaled)**2).sum()**.5
                leaf_l2_median_dists.append(leaf_l2_dist_to_median)
            leaf_scores = np.array(leaf_scores)
            leaf_l2_median_dists = np.array(leaf_l2_median_dists)
            leaf_logpdf_list = np.array(leaf_logpdf_list)
            leaf_kde_scores = np.array(leaf_kde_scores)
            if leaf_selection == "kde_max":
                leaf = leaves[np.argmax(leaf_kde_scores)]
                leaf_data_X = X[leaves_of_training_data == leaf]
            if leaf_selection == "normal_max":
                leaf = leaves[np.argmax(leaf_logpdf_list)]
                leaf_data_X = X[leaves_of_training_data == leaf]
            elif leaf_selection == "prob":
                leaf_probs = leaf_scores/leaf_scores.sum()
                leaf = np.random.choice(leaves,p=leaf_probs)
                leaf_data_X = X[leaves_of_training_data == leaf]
            elif leaf_selection == "dist_prob":
                leaf_l2_median_dists_probs = leaf_l2_median_dists/leaf_l2_median_dists.sum()
                leaf = np.random.choice(leaves,p=leaf_l2_median_dists_probs)
                leaf_data_X = X[leaves_of_training_data == leaf]
            elif leaf_selection == "dist_max":
                leaf = leaves[np.argmax(leaf_l2_median_dists)]
                leaf_data_X = X[leaves_of_training_data == leaf]
            
            while True:
                response_mean = leaf_data_X.mean(0)
                response_std = leaf_data_X.std(0)
                if sampling_method["type"] == "ind_gaussian":
                    response = np.random.normal(response_mean,response_std).reshape(1,-1) # Çoklu sample'la dene
                elif sampling_method["type"] == "uniform":
                    response = leaf_data_X.min(0)+(leaf_data_X.max(0)-leaf_data_X.min(0))*np.random.rand(leaf_data_X.shape[1])
                    response = response.reshape(1,-1)
                if is_bounded:
                    if ((response>=INPUT_MIN).all() &
                    (response<=INPUT_MAX).all()): 
                        break
                else:
                    if (response >= 0).all():
                        break
            return response
        else:
            response_all = []
            for leaf in leaves:
                leaf_data_Y = Y_scaled[leaves_of_training_data == leaf]
                leaf_mean,leaf_var = leaf_data_Y.mean(0),leaf_data_Y.var(0)
                leaf_l2_dist_to_median = (((leaf_data_Y - Y_target_scaled)**2).sum(1)**.5).min()
                leaf_l2_median_dists.append(leaf_l2_dist_to_median)
            leaf_l2_median_dists = np.array(leaf_l2_median_dists)

            for leaf in leaves:
                if leaf_selection == "dist_max":
                    if leaf != leaves[np.argmin(leaf_l2_median_dists)]:
                        continue
                leaf_data_X = X[leaves_of_training_data == leaf]
                response_all_leaf = None
                while True:
                    response_mean = leaf_data_X.mean(0)
                    response_std = leaf_data_X.std(0)
                    if sampling_method["type"] == "ind_gaussian":
                        response_added = np.random.multivariate_normal(response_mean,np.eye(len(response_std))*response_std**2,size=100)
                    elif sampling_method["type"] == "uniform":
                        response_added = leaf_data_X.min(0)+(leaf_data_X.max(0)-leaf_data_X.min(0))*np.random.rand(sample_per_leaf,leaf_data_X.shape[1])
                        # response = response.reshape(1,-1)
                    is_bounded = ((response_added>=INPUT_MIN).all(1) & (response_added<=INPUT_MAX).all(1))
                    response_added  = response_added[is_bounded]
                    if len(response_added > 0):
                        if response_all_leaf is not None:
                            response_all_leaf = np.vstack([response_all_leaf,response_added])
                        else:
                            response_all_leaf = response_added.copy()
                    if  len(response_all_leaf) >= sample_per_leaf:
                        response_all_leaf = response_all_leaf[:sample_per_leaf]
                        response_all.append(response_all_leaf)
                        break
            response_all = np.vstack(response_all)

            if sampling_method["acquisition"] == "TargetPCA&MinInputDist":
                X_min,X_max = X.min(0),X.max(0)
                X_scaled = (X-X_min)/(X_max-X_min)

                response_all_scaled = (response_all-X_min)/(X_max-X_min)
                response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
                response_all_dists_to_X_min_scaled = response_all_dists_to_X_min/response_all_dists_to_X_min.max()
                
                response_target_dists = ((self.fw_model.predict(response_all)-Y_target.reshape(1,-1))**2).sum(1)**.5
                response_target_dists_scaled = response_target_dists/response_target_dists.max()

                acquisition = 0.5*response_target_dists_scaled+0.5*(1-response_all_dists_to_X_min_scaled)
                
                response = response_all[acquisition.argmax()].reshape(1,-1)
                return response
            elif sampling_method["acquisition"] == "MaxOfMinInputDist":
                X_min,X_max = X.min(0),X.max(0)
                X_scaled = (X-X_min)/(X_max-X_min)

                response_all_scaled = (response_all-X_min)/(X_max-X_min)
                response_all_dists_to_X_min = euclidean_distances(response_all_scaled,X_scaled).min(1)
                response_all_dists_to_X_min_scaled = response_all_dists_to_X_min/response_all_dists_to_X_min.max()
                
                acquisition = response_all_dists_to_X_min_scaled.copy()
                
                response = response_all[acquisition.argmax()].reshape(1,-1)
                return response


            return response_all

class BayesianOptimization:
    def __init__(self,sampler,metric) -> None:
        if sampler == "TPESampler":
            sampler_func = optuna.samplers.TPESampler(seed=1)
        elif sampler == "GPSampler":
            sampler_func = optuna.samplers.GPSampler(seed=1)

        self.study = optuna.create_study(sampler=sampler_func)
        self.current_perf = 0
        self.metric = metric
        pass

    def store_initials_data(self,X,Y,s,e,t):
        self.X = X
        self.Y = Y
        self.s = s
        self.e = e
        self.t = t

    def add_initials_manually(self,idx):
        X = self.X[idx]
        Y = self.Y[idx]
        s = self.s
        e = self.e
        t = self.t
        if self.metric == "perf":
            metrics = -calculate_perf(Y,s,e,t)
        elif self.metric == "mse":
            metrics = (Y[:,s:e+1]**2).mean(1)
        for i in range(X.shape[0]):
            optuna_params,optuna_distributions = {},{}
            optuna_value=metrics[i]
            for j in range(X.shape[1]):
                excel_col_name = EXCEL_COLUMN_ORDER[j]
                hfss_var_name = PARAM_NAMES_DATA2CODE[excel_col_name]
                optuna_params[hfss_var_name] = X[i,j]
                optuna_distributions[hfss_var_name] = optuna.distributions.FloatDistribution(INPUT_LIMITS[excel_col_name]["min"],INPUT_LIMITS[excel_col_name]["max"])
            self.study.add_trial(
                optuna.trial.create_trial(
                    params=optuna_params,
                    distributions=optuna_distributions,
                    value=optuna_value,
                )
            )

    def set_limits(self,input_min,input_max):
        self.input_min = input_min
        self.input_max = input_max

    def set_parameters(self,params):
        self.input_params = params
    def get_parameters(self):
        return self.input_params
    
    def objective(self,trial):
        hfss_vars = []
        for i in range(len(self.input_min)):
            hfss_vars.append(trial.suggest_float(PARAM_NAMES_DATA2CODE[EXCEL_COLUMN_ORDER[i]],self.input_min[i],self.input_max[i]))
        
        self.set_parameters(np.array(hfss_vars))
        return None  # An objective value linked with the Trial object.

    def run_study(self):
        self.study.optimize(lambda trial:self.objective(trial), n_trials=1)

        

def create_logger(log_filepath):
    logging.basicConfig(filename=log_filepath,
                        level=logging.WARNING,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    logger.addHandler(console)



# Neural Network Structure
class addCoords_1D(nn.Module):
   def __init__(self):
       super(addCoords_1D, self).__init__()

   def forward(self, out):
       in_batch, in_ch, in_w = out.shape        
       width_coords = torch.linspace(-1, 1, steps=in_w).to(out.device)   
       wc = width_coords.repeat(in_batch, 1, 1)
       coord_x = torch.cat((out, wc), 1)
       return coord_x
   
class NeuralNet(nn.Module):
    def __init__(self):
        super(NeuralNet, self).__init__()
        self.logsigma = nn.Parameter(torch.ones(1))
        self.filter_size = 41
        
        self.add_coords = addCoords_1D()
        
        self.linear = nn.Sequential(
            nn.Linear(11, 60),                                
            nn.Tanh(), 
            
            nn.Linear(60, 60),            
            nn.Tanh(),  
            
            nn.Linear(60, 60),            
            nn.Tanh(), 
                                   
        )                  
                               
        self.deconv1 = nn.Sequential(
            nn.ConvTranspose1d(in_channels= 60 , out_channels= 40 , kernel_size=21, stride=1),                     
            nn.Tanh(), 
                                             
        )     
        self.deconv2 = nn.Sequential(
            nn.ConvTranspose1d(in_channels= 40 , out_channels=40, kernel_size=7, stride=3),             
            nn.Tanh(),   
                           
        )
        self.deconv3 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=41, out_channels=2, kernel_size=3, stride=3),             
            nn.Tanh(), 
                    
        )                        
         
    def smooth(self, x):
            
             # First define a global variable for the size of the Gaussian filter. 
             # Here, filter_size is one half of the filter. This is a hyperparameter to tune.
             N = self.filter_size
             
            
             # Pad the input tensor to preserve the dimension
             x = F.pad(x, ((N-1)//2, (N-1)//2), mode='reflect')
             
             # Use the natural log of sigma as the variable for scaling.
             sigma = torch.exp(self.logsigma).unsqueeze(-1).unsqueeze(-1) # Tensor size N_channelx1x1
             sigma = sigma.repeat((1, 1, N))# Tensor size N_channelxN_channelxfilter_size
             
             # Set the total width of the Gaussian filter as 6*sigma
             hw = 3*sigma
             # Generate a vector between 0 and 1
             xx = torch.linspace(0,1,steps=N).unsqueeze(0).unsqueeze(0).to("cpu")# Tensor size 1x1xfilter_size
             xx = xx.repeat((x.shape[1], 1,1))# Tensor size N_channelxN_channelxfilter_size
             # Shift xx for every channel 
             xx = 2*hw*xx-hw # Tensor size N_channelxN_channelxfilter_size
             
             # Generate the Gaussian filter
             gauss = 1/(2*math.pi*sigma**2)*torch.exp(-1/(2*(sigma**2))*xx**2)# Tensor size N_channelxN_channelxfilter_size
             
             # Find the sum of the coeffcients
             gauss_sum = gauss.sum(dim=2).unsqueeze(-1)# Tensor size N_channelxN_channelx1
             gauss_sum = gauss_sum.repeat((1, 1, gauss.shape[-1]))# Tensor size N_channelxN_channelxfilter_size
             # Normalize the filter
             gauss = gauss/gauss_sum # Tensor size N_channelxN_channelxfilter_size
             output = F.conv1d(x, gauss, groups=x.shape[1] )
             
             return output  
         
    def forward(self, x):

        out = self.linear(x)

        out = out.view(len(x), 60 , 1)

        out = self.deconv1(out)
        
        out = self.deconv2(out)
        
        out = self.add_coords(out)
        
        out = self.deconv3(out)  
                              
        out = self.smooth(out)
       
        return out