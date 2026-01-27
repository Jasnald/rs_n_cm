# -*- coding: utf-8 -*-

class ExpProcessor(object):
    
    @staticmethod
    def get_average(values):

        if not values: return 0.0
        return sum(values) / float(len(values))

    @staticmethod
    def process_t_shape(raw_data):

        meas = raw_data.get('measurements', {})

        avg = {}
        for key, vals in meas.items():
            avg[key] = ExpProcessor.get_average(vals)

        base_thick = (avg.get('bottom_thickness_left', 0) + 
                      avg.get('bottom_thickness_right', 0)) / 2.0
        
        v_height = avg.get('total_height', 0) - base_thick
        
        return {
            'h_width': avg.get('bottom_width', 0),
            'h_thickness': base_thick,
            'v_width': avg.get('wall_width', 0),
            'v_height': v_height,
            'offset_1': avg.get('flange_left', 0)
        }
    
    @staticmethod
    def process_block_shape(raw_data):

        meas = raw_data.get('measurements', {})

        avg = {}
        for key, vals in meas.items():
            avg[key] = ExpProcessor.get_average(vals)

        return {
            "avg_lenth":  avg.get("lenth", 0),
            "avg_width":  avg.get("width", 0),
            "avg_height": avg.get("height", 0),
            "avg_cut":    avg.get("cut", 0)
        }