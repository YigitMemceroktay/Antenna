$begin 'Profile'
	$begin 'ProfileGroup'
		MajorVer=2024
		MinorVer=2
		Name='Solution Process'
		$begin 'StartInfo'
			I(1, 'Start Time', '02/28/2026 15:12:36')
			I(1, 'Host', 'SIMPL-DZ11-2')
			I(1, 'Processor', '32')
			I(1, 'OS', 'NT 10.0')
			I(1, 'Product', 'HFSS Version 2024.2.0')
		$end 'StartInfo'
		$begin 'TotalInfo'
			I(1, 'Elapsed Time', '00:02:03')
			I(1, 'ComEngine Memory', '77.4 M')
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
		ProfileItem('Design Validation', 0, 0, 0, 0, 0, 'I(1, 0, \'Elapsed time : 00:00:00 , HFSS ComEngine Memory : 70.7 M\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Perform full validations with standard port validations\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Initial Meshing'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:12:36')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:06')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('Mesh', 4, 0, 4, 0, 55000, 'I(3, 2, \'Tetrahedra\', 17890, false, 1, \'Type\', \'TAU\', 2, \'Cores\', 4, false)', true, true)
			ProfileItem('Coarsen', 1, 0, 1, 0, 55000, 'I(1, 2, \'Tetrahedra\', 2556, false)', true, true)
			ProfileItem('Lambda Refine', 0, 0, 0, 0, 28332, 'I(2, 2, \'Tetrahedra\', 4134, false, 2, \'Cores\', 1, false)', true, true)
			ProfileItem('Simulation Setup', 0, 0, 0, 0, 180936, 'I(1, 1, \'Disk\', \'0 Bytes\')', true, true)
			ProfileItem('Port Adapt', 0, 0, 0, 0, 189340, 'I(2, 2, \'Tetrahedra\', 3282, false, 1, \'Disk\', \'3.72 KB\')', true, true)
			ProfileItem('Port Refine', 0, 0, 0, 0, 23304, 'I(2, 2, \'Tetrahedra\', 4217, false, 2, \'Cores\', 1, false)', true, true)
		$end 'ProfileGroup'
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Adaptive Meshing'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:12:43')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:01:08')
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
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 184144, 'I(2, 2, \'Tetrahedra\', 3365, false, 1, \'Disk\', \'3.37 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 1, 0, 221464, 'I(3, 2, \'Tetrahedra\', 3365, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'34 KB\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 1, 0, 288220, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 23855, false, 3, \'Matrix bandwidth\', 20.0941, \'%5.1f\', 1, \'Disk\', \'96.2 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 288220, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'584 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 75172, 'I(1, 0, \'Adaptive Pass 1\')', true, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 25900, 'I(2, 2, \'Tetrahedra\', 5229, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 185892, 'I(2, 2, \'Tetrahedra\', 4219, false, 1, \'Disk\', \'3.37 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 1, 0, 232848, 'I(3, 2, \'Tetrahedra\', 4219, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 1, 0, 326424, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 29563, false, 3, \'Matrix bandwidth\', 20.3667, \'%5.1f\', 1, \'Disk\', \'23.7 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 326424, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'333 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 75440, 'I(1, 0, \'Adaptive Pass 2\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.802773, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 27580, 'I(2, 2, \'Tetrahedra\', 6499, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 188244, 'I(2, 2, \'Tetrahedra\', 5238, false, 1, \'Disk\', \'3.37 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 1, 0, 245628, 'I(3, 2, \'Tetrahedra\', 5238, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 2, 0, 371132, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 36515, false, 3, \'Matrix bandwidth\', 20.5234, \'%5.1f\', 1, \'Disk\', \'28.6 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 371132, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'370 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76080, 'I(1, 0, \'Adaptive Pass 3\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.965287, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 29220, 'I(2, 2, \'Tetrahedra\', 8072, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 191972, 'I(2, 2, \'Tetrahedra\', 6554, false, 1, \'Disk\', \'3.37 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 1, 0, 260800, 'I(3, 2, \'Tetrahedra\', 6554, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 3, 0, 422064, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 45401, false, 3, \'Matrix bandwidth\', 20.6844, \'%5.1f\', 1, \'Disk\', \'36.1 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 422064, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'427 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76228, 'I(1, 0, \'Adaptive Pass 4\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.337154, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 31164, 'I(2, 2, \'Tetrahedra\', 10039, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 196428, 'I(2, 2, \'Tetrahedra\', 8259, false, 1, \'Disk\', \'3.37 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 1, 0, 281332, 'I(3, 2, \'Tetrahedra\', 8259, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'1 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 3, 0, 489028, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 56733, false, 3, \'Matrix bandwidth\', 20.8597, \'%5.1f\', 1, \'Disk\', \'45.7 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 489028, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'501 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76300, 'I(1, 0, \'Adaptive Pass 5\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.155801, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 33900, 'I(2, 2, \'Tetrahedra\', 12521, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 201348, 'I(2, 2, \'Tetrahedra\', 10404, false, 1, \'Disk\', \'3.37 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 2, 0, 307412, 'I(3, 2, \'Tetrahedra\', 10404, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 4, 0, 571736, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 71029, false, 3, \'Matrix bandwidth\', 20.9923, \'%5.1f\', 1, \'Disk\', \'57.3 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 571736, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'589 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76400, 'I(1, 0, \'Adaptive Pass 6\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.091033, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 37636, 'I(2, 2, \'Tetrahedra\', 15646, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 207500, 'I(2, 2, \'Tetrahedra\', 13167, false, 1, \'Disk\', \'6.49 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 2, 0, 341220, 'I(3, 2, \'Tetrahedra\', 13167, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 2, 0, 5, 0, 692048, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 89279, false, 3, \'Matrix bandwidth\', 21.1292, \'%5.1f\', 1, \'Disk\', \'72.7 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 692048, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'708 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76504, 'I(1, 0, \'Adaptive Pass 7\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0597549, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 41676, 'I(2, 2, \'Tetrahedra\', 19387, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 216308, 'I(2, 2, \'Tetrahedra\', 16449, false, 1, \'Disk\', \'6.49 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 379784, 'I(3, 2, \'Tetrahedra\', 16449, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 2, 0, 8, 0, 858972, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 111017, false, 3, \'Matrix bandwidth\', 21.2273, \'%5.1f\', 1, \'Disk\', \'86.3 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 858972, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'825 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76476, 'I(1, 0, \'Adaptive Pass 8\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0336825, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 42816, 'I(2, 2, \'Tetrahedra\', 22353, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 223020, 'I(2, 2, \'Tetrahedra\', 19090, false, 1, \'Disk\', \'6.49 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 412508, 'I(3, 2, \'Tetrahedra\', 19090, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 8, 0, 954380, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 128451, false, 3, \'Matrix bandwidth\', 21.289, \'%5.1f\', 1, \'Disk\', \'69.5 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 954380, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'807 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76484, 'I(1, 0, \'Adaptive Pass 9\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0210028, \'%.5f\')', false, true)
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
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 41960, 'I(2, 2, \'Tetrahedra\', 24108, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 226388, 'I(2, 2, \'Tetrahedra\', 20721, false, 1, \'Disk\', \'9.6 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 430420, 'I(3, 2, \'Tetrahedra\', 20721, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 9, 0, 1017368, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 139077, false, 3, \'Matrix bandwidth\', 21.3349, \'%5.1f\', 1, \'Disk\', \'42.9 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 1017368, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'728 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76492, 'I(1, 0, \'Adaptive Pass 10\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.01011, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 11'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 42472, 'I(2, 2, \'Tetrahedra\', 25665, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 229208, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'9.6 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 446872, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 11, 0, 1101316, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'37.6 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 1101316, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'731 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76496, 'I(1, 0, \'Adaptive Pass 11\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.00730584, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileFootnote('I(1, 0, \'Adaptive Passes converged\')', 0)
		$end 'ProfileGroup'
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Frequency Sweep'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:13:51')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:48')
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
					I(1, 'Time', '02/28/2026 15:13:51')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(1, 'Elapsed Time', '00:00:48')
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
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 255580, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 326928, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1172588, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1172588, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 28GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 255716, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 326432, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1171384, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1171384, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 25.5GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253120, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 323728, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1168992, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1168992, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 30.5GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 252584, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 323408, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1169012, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1169012, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 1, Frequency: 33GHz; Additional basis points are needed before the interpolation error can be computed.\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 2, Frequency: 23GHz; Additional basis points are needed before the interpolation error can be computed.\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 3, Frequency: 28GHz; S Matrix Error =  45.232%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 4, Frequency: 25.5GHz; S Matrix Error =  32.833%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 5, Frequency: 30.5GHz; S Matrix Error =  38.389%\')', false, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 31.75GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253804, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324920, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1169704, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1169704, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 29.25GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:12')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 254488, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 325904, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1171052, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1171052, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 26.75GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253096, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324516, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1168916, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1168916, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 24.25GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253360, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324220, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1170468, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1170468, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 6, Frequency: 31.75GHz; S Matrix Error =   6.499%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 7, Frequency: 29.25GHz; S Matrix Error =   1.126%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 8, Frequency: 26.75GHz; S Matrix Error =   0.211%; Secondary solver criterion is not converged\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 9, Frequency: 24.25GHz; S Matrix Error =   0.286%; Secondary solver criterion is not converged\')', false, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 78764, 'I(1, 0, \'Frequency Group #2; Interpolating frequency sweep\')', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 32.375GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 254276, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 325516, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1170992, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1170992, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 29.875GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 254552, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 325420, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1170640, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1170640, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 31.125GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253024, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324528, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1170100, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1170100, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 28.625GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253264, 'I(2, 2, \'Tetrahedra\', 22136, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324264, 'I(3, 2, \'Tetrahedra\', 22136, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1170328, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 148349, false, 3, \'Matrix bandwidth\', 21.3636, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1170328, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'202 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 10, Frequency: 32.375GHz; S Matrix Error =   0.117%; Secondary solver criterion is not converged\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 11, Frequency: 29.875GHz; Scattering matrix quantities converged; Passive within tolerance\')', false, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 78876, 'I(1, 0, \'Frequency Group #3; Interpolating frequency sweep\')', true, true)
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
			ProfileItem('Design Validation', 0, 0, 0, 0, 0, 'I(2, 1, \'Elapsed Time\', \'00:00:00\', 1, \'Total Memory\', \'70.7 MB\')', false, true)
			ProfileItem('Initial Meshing', 0, 0, 0, 0, 0, 'I(2, 1, \'Elapsed Time\', \'00:00:06\', 1, \'Total Memory\', \'239 MB\')', false, true)
			ProfileItem('Adaptive Meshing', 0, 0, 0, 0, 0, 'I(5, 1, \'Elapsed Time\', \'00:01:08\', 1, \'Average memory/process\', \'1.05 GB\', 1, \'Max memory/process\', \'1.05 GB\', 2, \'Max number of processes/frequency\', 1, false, 2, \'Total number of cores\', 4, false)', false, true)
			ProfileItem('Frequency Sweep', 0, 0, 0, 0, 0, 'I(5, 1, \'Elapsed Time\', \'00:00:48\', 1, \'Average memory/process\', \'1.12 GB\', 1, \'Max memory/process\', \'1.12 GB\', 2, \'Max number of processes/frequency\', 1, false, 2, \'Total number of cores\', 4, false)', false, true)
			ProfileFootnote('I(3, 2, \'Max solved tets\', 22136, false, 2, \'Max matrix size\', 148349, false, 1, \'Matrix bandwidth\', \'21.4\')', 0)
		$end 'ProfileGroup'
		ProfileFootnote('I(2, 1, \'Stop Time\', \'02/28/2026 15:14:39\', 1, \'Status\', \'Normal Completion\')', 0)
	$end 'ProfileGroup'
$end 'Profile'
