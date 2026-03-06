$begin 'Profile'
	$begin 'ProfileGroup'
		MajorVer=2024
		MinorVer=2
		Name='Solution Process'
		$begin 'StartInfo'
			I(1, 'Start Time', '02/28/2026 15:07:57')
			I(1, 'Host', 'SIMPL-DZ11-2')
			I(1, 'Processor', '32')
			I(1, 'OS', 'NT 10.0')
			I(1, 'Product', 'HFSS Version 2024.2.0')
		$end 'StartInfo'
		$begin 'TotalInfo'
			I(1, 'Elapsed Time', '00:01:30')
			I(1, 'ComEngine Memory', '77.3 M')
		$end 'TotalInfo'
		GroupOptions=8
		TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'Executing From\', \'C:\\\\Program Files\\\\AnsysEM\\\\v242\\\\Win64\\\\HFSSCOMENGINE.exe\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='HPC'
			$begin 'StartInfo'
				I(1, 'Type', 'Auto')
				I(1, 'MPI Vendor', 'Intel')
				I(1, 'MPI Version', '2021')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(0, ' ')
			$end 'TotalInfo'
			GroupOptions=0
			TaskDataOptions(Memory=8)
			ProfileItem('Machine', 0, 0, 0, 0, 0, 'I(5, 1, \'Name\', \'simpl-dz11-2\', 1, \'Memory\', \'384 GB\', 3, \'RAM Limit\', 90, \'%f%%\', 2, \'Cores\', 4, false, 1, \'Free Disk Space\', \'76.5 GB\')', false, true)
		$end 'ProfileGroup'
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'Allow off core\', \'True\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'Solution Basis Order\', \'1\')', false, true)
		ProfileItem('Design Validation', 0, 0, 0, 0, 0, 'I(1, 0, \'Elapsed time : 00:00:00 , HFSS ComEngine Memory : 70.9 M\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Perform full validations with standard port validations\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Initial Meshing'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:07:57')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:07')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('Mesh', 4, 0, 5, 0, 58000, 'I(3, 2, \'Tetrahedra\', 19959, false, 1, \'Type\', \'TAU\', 2, \'Cores\', 4, false)', true, true)
			ProfileItem('Coarsen', 1, 0, 1, 0, 58000, 'I(1, 2, \'Tetrahedra\', 2208, false)', true, true)
			ProfileItem('Lambda Refine', 0, 0, 0, 0, 27916, 'I(2, 2, \'Tetrahedra\', 3598, false, 2, \'Cores\', 1, false)', true, true)
			ProfileItem('Simulation Setup', 0, 0, 0, 0, 180764, 'I(1, 1, \'Disk\', \'0 Bytes\')', true, true)
			ProfileItem('Port Adapt', 0, 0, 0, 0, 187180, 'I(2, 2, \'Tetrahedra\', 2978, false, 1, \'Disk\', \'2.87 KB\')', true, true)
			ProfileItem('Port Refine', 0, 0, 0, 0, 22112, 'I(2, 2, \'Tetrahedra\', 3619, false, 2, \'Cores\', 1, false)', true, true)
		$end 'ProfileGroup'
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Adaptive Meshing'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:08:04')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:50')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 1'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 182344, 'I(2, 2, \'Tetrahedra\', 2999, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 0, 0, 216504, 'I(3, 2, \'Tetrahedra\', 2999, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'33.1 KB\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 1, 0, 284868, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 20939, false, 3, \'Matrix bandwidth\', 20.4141, \'%5.1f\', 1, \'Disk\', \'84.8 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 284868, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'501 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 75484, 'I(1, 0, \'Adaptive Pass 1\')', true, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 2'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 25124, 'I(2, 2, \'Tetrahedra\', 4525, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 184460, 'I(2, 2, \'Tetrahedra\', 3752, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 0, 0, 225668, 'I(3, 2, \'Tetrahedra\', 3752, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 1, 0, 316376, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 25999, false, 3, \'Matrix bandwidth\', 20.5875, \'%5.1f\', 1, \'Disk\', \'21.2 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 316376, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'275 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 75668, 'I(1, 0, \'Adaptive Pass 2\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.63096, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 3'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 26204, 'I(2, 2, \'Tetrahedra\', 5652, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 186384, 'I(2, 2, \'Tetrahedra\', 4719, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 238060, 'I(3, 2, \'Tetrahedra\', 4719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 2, 0, 355060, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 32435, false, 3, \'Matrix bandwidth\', 20.7798, \'%5.1f\', 1, \'Disk\', \'26.6 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 355060, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'316 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76112, 'I(1, 0, \'Adaptive Pass 3\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.23784, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 4'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 27772, 'I(2, 2, \'Tetrahedra\', 7074, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 189280, 'I(2, 2, \'Tetrahedra\', 5959, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 251864, 'I(3, 2, \'Tetrahedra\', 5959, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 2, 0, 403916, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 40673, false, 3, \'Matrix bandwidth\', 20.9416, \'%5.1f\', 1, \'Disk\', \'33.6 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 403916, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'367 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76232, 'I(1, 0, \'Adaptive Pass 4\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.165002, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 5'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 29768, 'I(2, 2, \'Tetrahedra\', 8865, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 194012, 'I(2, 2, \'Tetrahedra\', 7532, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 271696, 'I(3, 2, \'Tetrahedra\', 7532, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 3, 0, 461944, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 51079, false, 3, \'Matrix bandwidth\', 21.0877, \'%5.1f\', 1, \'Disk\', \'42.1 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 461944, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'433 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76468, 'I(1, 0, \'Adaptive Pass 5\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.131956, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 6'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 32236, 'I(2, 2, \'Tetrahedra\', 11125, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 198532, 'I(2, 2, \'Tetrahedra\', 9547, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 295040, 'I(3, 2, \'Tetrahedra\', 9547, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 4, 0, 545184, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 64387, false, 3, \'Matrix bandwidth\', 21.2104, \'%5.1f\', 1, \'Disk\', \'53.4 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 545184, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'521 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76568, 'I(1, 0, \'Adaptive Pass 6\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0773884, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 7'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 35576, 'I(2, 2, \'Tetrahedra\', 13851, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 203652, 'I(2, 2, \'Tetrahedra\', 11982, false, 1, \'Disk\', \'4.33 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 2, 0, 324912, 'I(3, 2, \'Tetrahedra\', 11982, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 5, 0, 666840, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 80467, false, 3, \'Matrix bandwidth\', 21.3027, \'%5.1f\', 1, \'Disk\', \'64.2 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 666840, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'619 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76580, 'I(1, 0, \'Adaptive Pass 7\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0309781, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 8'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 37184, 'I(2, 2, \'Tetrahedra\', 16610, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 209876, 'I(2, 2, \'Tetrahedra\', 14477, false, 1, \'Disk\', \'8.4 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 2, 0, 355180, 'I(3, 2, \'Tetrahedra\', 14477, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 2, 0, 7, 0, 766972, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 96843, false, 3, \'Matrix bandwidth\', 21.3809, \'%5.1f\', 1, \'Disk\', \'65.4 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 766972, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'675 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76596, 'I(1, 0, \'Adaptive Pass 8\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.019829, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 9'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 38032, 'I(2, 2, \'Tetrahedra\', 18563, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 213840, 'I(2, 2, \'Tetrahedra\', 16283, false, 1, \'Disk\', \'8.4 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 2, 0, 374912, 'I(3, 2, \'Tetrahedra\', 16283, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 2, 0, 8, 0, 854256, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 108665, false, 3, \'Matrix bandwidth\', 21.4284, \'%5.1f\', 1, \'Disk\', \'47.6 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 854256, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'638 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76608, 'I(1, 0, \'Adaptive Pass 9\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0128808, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 10'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 43540, 'I(2, 2, \'Tetrahedra\', 22308, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 222988, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'8.41 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 416968, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 10, 0, 1017688, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'89.2 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 1017688, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'884 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76608, 'I(1, 0, \'Adaptive Pass 10\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.00788412, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileFootnote('I(1, 0, \'Adaptive Passes converged\')', 0)
		$end 'ProfileGroup'
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Frequency Sweep'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:08:55')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:32')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'HPC\', \'Enabled\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Solution - Sweep'
				$begin 'StartInfo'
					I(0, 'Interpolating HFSS Frequency Sweep, Solving Distributed - up to 4 frequencies in parallel')
					I(1, 'Time', '02/28/2026 15:08:55')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(1, 'Elapsed Time', '00:00:32')
				$end 'TotalInfo'
				GroupOptions=4
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'From 23GHz to 33GHz, 201 Frequencies\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Frequency: 33GHz has already been solved\')', false, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 23GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 246564, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 311368, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1077992, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1077992, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 28GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 246984, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 311084, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1077948, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1077948, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 25.5GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 245920, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 310608, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1075708, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1075708, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 30.5GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 245684, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 310460, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1075924, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1075924, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 1, Frequency: 33GHz; Additional basis points are needed before the interpolation error can be computed.\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 2, Frequency: 23GHz; Additional basis points are needed before the interpolation error can be computed.\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 3, Frequency: 28GHz; S Matrix Error = 136.704%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 4, Frequency: 25.5GHz; S Matrix Error =  41.729%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 5, Frequency: 30.5GHz; S Matrix Error =   1.878%\')', false, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 31.75GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:09')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 248020, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 312976, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1078124, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1078124, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 29.25GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 248480, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 1, 0, 313216, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1078956, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1078956, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 26.75GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 245880, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 1, 0, 310832, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1075724, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1075724, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 24.25GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 245660, 'I(2, 2, \'Tetrahedra\', 19719, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 1, 0, 310428, 'I(3, 2, \'Tetrahedra\', 19719, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1074704, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 131133, false, 3, \'Matrix bandwidth\', 21.4973, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1074704, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'179 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 6, Frequency: 31.75GHz; S Matrix Error =   0.097%; Secondary solver criterion is not converged\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 7, Frequency: 29.25GHz; Scattering matrix quantities converged; Passive within tolerance\')', false, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 78752, 'I(1, 0, \'Frequency Group #2; Interpolating frequency sweep\')', true, true)
				ProfileFootnote('I(1, 0, \'Interpolating sweep converged and is passive\')', 0)
				ProfileFootnote('I(1, 0, \'HFSS: Distributed Interpolating sweep\')', 0)
			$end 'ProfileGroup'
		$end 'ProfileGroup'
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Simulation Summary'
			$begin 'StartInfo'
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(0, ' ')
			$end 'TotalInfo'
			GroupOptions=0
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('Design Validation', 0, 0, 0, 0, 0, 'I(2, 1, \'Elapsed Time\', \'00:00:00\', 1, \'Total Memory\', \'70.9 MB\')', false, true)
			ProfileItem('Initial Meshing', 0, 0, 0, 0, 0, 'I(2, 1, \'Elapsed Time\', \'00:00:07\', 1, \'Total Memory\', \'239 MB\')', false, true)
			ProfileItem('Adaptive Meshing', 0, 0, 0, 0, 0, 'I(5, 1, \'Elapsed Time\', \'00:00:50\', 1, \'Average memory/process\', \'994 MB\', 1, \'Max memory/process\', \'994 MB\', 2, \'Max number of processes/frequency\', 1, false, 2, \'Total number of cores\', 4, false)', false, true)
			ProfileItem('Frequency Sweep', 0, 0, 0, 0, 0, 'I(5, 1, \'Elapsed Time\', \'00:00:32\', 1, \'Average memory/process\', \'1.03 GB\', 1, \'Max memory/process\', \'1.03 GB\', 2, \'Max number of processes/frequency\', 1, false, 2, \'Total number of cores\', 4, false)', false, true)
			ProfileFootnote('I(3, 2, \'Max solved tets\', 19719, false, 2, \'Max matrix size\', 131133, false, 1, \'Matrix bandwidth\', \'21.5\')', 0)
		$end 'ProfileGroup'
		ProfileFootnote('I(2, 1, \'Stop Time\', \'02/28/2026 15:09:27\', 1, \'Status\', \'Normal Completion\')', 0)
	$end 'ProfileGroup'
$end 'Profile'
